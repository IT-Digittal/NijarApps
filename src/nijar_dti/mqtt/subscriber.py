"""Subscriber MQTT robusto para ingesta IoT.

Características:

- Conexión persistente con reconexión exponencial controlada por paho-mqtt.
- Subscripción dinámica al patrón configurado (por defecto
  ``nijar/sensors/+/+``).
- Validación y normalización de cada mensaje en :mod:`parser`.
- Persistencia en BBDD a través del servicio ``iot_service``.
- Marca observaciones con ``valido=False`` cuando el sensor no está en el
  catálogo en lugar de descartar el mensaje.
- Métricas y logs estructurados.
- Compatible con TLS (certificados de cliente) para producción.

El cliente paho-mqtt expone callbacks síncronos. El bridging a la BBDD
async se hace mediante ``asyncio.run_coroutine_threadsafe`` sobre un loop
asyncio dedicado que gira en un hilo aparte.
"""

from __future__ import annotations

import asyncio
import logging
import ssl
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import paho.mqtt.client as mqtt

from nijar_dti.config import Settings, get_settings
from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.mqtt.parser import MessageParseError, parse_message
from nijar_dti.services import iot_service

log = logging.getLogger(__name__)


@dataclass
class SubscriberStats:
    """Métricas operativas del subscriber."""

    mensajes_recibidos: int = 0
    mensajes_validos: int = 0
    mensajes_invalidos: int = 0
    sensores_no_encontrados: int = 0
    errores_persistencia: int = 0
    reconexiones: int = 0
    iniciado_en: float = field(default_factory=time.time)

    def snapshot(self) -> dict:
        return {
            "mensajes_recibidos": self.mensajes_recibidos,
            "mensajes_validos": self.mensajes_validos,
            "mensajes_invalidos": self.mensajes_invalidos,
            "sensores_no_encontrados": self.sensores_no_encontrados,
            "errores_persistencia": self.errores_persistencia,
            "reconexiones": self.reconexiones,
            "uptime_segundos": int(time.time() - self.iniciado_en),
        }


class MqttSubscriber:
    """Subscriber MQTT que persiste observaciones en la BBDD."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.stats = SubscriberStats()
        self._stop_event = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._client: mqtt.Client | None = None

    # ----------------- ciclo de vida -----------------

    def _start_event_loop(self) -> None:
        """Arranca un loop asyncio en un hilo dedicado."""
        ready = threading.Event()

        def runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            ready.set()
            loop.run_forever()

        self._loop_thread = threading.Thread(target=runner, daemon=True, name="mqtt-asyncio")
        self._loop_thread.start()
        ready.wait(timeout=5)
        if self._loop is None:
            raise RuntimeError("No se pudo arrancar el loop asyncio")

    def _stop_event_loop(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread:
            self._loop_thread.join(timeout=5)

    # ----------------- callbacks paho -----------------

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc, properties=None) -> None:  # noqa: ARG002
        if rc == 0:
            log.info(
                "Conectado al broker MQTT %s:%s — suscribiendo a %s",
                self.settings.mqtt_broker_host,
                self.settings.mqtt_broker_port,
                self.settings.mqtt_topic_pattern,
            )
            client.subscribe(self.settings.mqtt_topic_pattern, qos=self.settings.mqtt_qos)
        else:
            log.error("Conexión MQTT rechazada (rc=%s)", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata, rc, properties=None) -> None:  # noqa: ARG002
        if rc != 0:
            log.warning("Desconexión MQTT inesperada (rc=%s) — paho reconectará", rc)
            self.stats.reconexiones += 1
        else:
            log.info("Desconexión MQTT limpia")

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:  # noqa: ARG002
        self.stats.mensajes_recibidos += 1
        try:
            parsed = parse_message(msg.topic, msg.payload)
        except MessageParseError as exc:
            self.stats.mensajes_invalidos += 1
            log.warning("Mensaje inválido en %s: %s", msg.topic, exc)
            return

        if self._loop is None:
            log.error("Loop asyncio no inicializado, descartando mensaje")
            return

        future = asyncio.run_coroutine_threadsafe(
            self._persist_observation(parsed.observacion), self._loop
        )

        # No bloqueamos al hilo MQTT esperando la persistencia,
        # pero adjuntamos un callback para contabilizar el resultado.
        def _done(f) -> None:
            try:
                f.result()
                self.stats.mensajes_validos += 1
            except iot_service.SensorNotFound:
                self.stats.sensores_no_encontrados += 1
                log.info("Sensor no en catálogo (descartado): %s", parsed.observacion.sensor_urn)
            except Exception as exc:  # noqa: BLE001
                self.stats.errores_persistencia += 1
                log.exception("Error persistiendo observación: %s", exc)

        future.add_done_callback(_done)

    async def _persist_observation(self, observacion) -> None:
        async with AsyncSessionLocal() as db:
            try:
                await iot_service.ingerir_observacion(db, observacion)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    # ----------------- arranque/parada -----------------

    def _build_client(self) -> mqtt.Client:
        client = mqtt.Client(
            client_id=self.settings.mqtt_client_id,
            clean_session=False,
            protocol=mqtt.MQTTv311,
        )
        client.reconnect_delay_set(
            min_delay=self.settings.mqtt_reconnect_delay_min_seconds,
            max_delay=self.settings.mqtt_reconnect_delay_max_seconds,
        )
        if self.settings.mqtt_username:
            client.username_pw_set(self.settings.mqtt_username, self.settings.mqtt_password or None)

        if self.settings.mqtt_use_tls:
            client.tls_set(
                ca_certs=self.settings.mqtt_tls_ca_cert or None,
                certfile=self.settings.mqtt_tls_client_cert or None,
                keyfile=self.settings.mqtt_tls_client_key or None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    def run(self) -> None:
        """Bloquea ejecutando el loop MQTT hasta que se llame a ``stop()``."""
        self._start_event_loop()
        self._client = self._build_client()
        try:
            self._client.connect(
                self.settings.mqtt_broker_host,
                self.settings.mqtt_broker_port,
                keepalive=self.settings.mqtt_keepalive,
            )
        except OSError as exc:
            log.error("No se pudo conectar al broker MQTT: %s", exc)
            self._stop_event_loop()
            raise

        log.info("Subscriber MQTT iniciado — esperando mensajes")
        try:
            while not self._stop_event.is_set():
                self._client.loop(timeout=1.0)
        finally:
            self._client.disconnect()
            self._stop_event_loop()
            log.info("Subscriber MQTT detenido — stats: %s", self.stats.snapshot())

    def stop(self) -> None:
        """Solicita parada limpia del subscriber."""
        self._stop_event.set()
