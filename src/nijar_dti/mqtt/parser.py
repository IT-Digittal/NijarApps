"""Parsing y validación de mensajes MQTT entrantes.

Esta capa es independiente del cliente MQTT y de la BBDD: recibe el
``topic`` y el ``payload`` en bytes y devuelve una ``ObservacionIn`` lista
para la ingesta. Toda la lógica está aquí para poder testearla sin
dependencias externas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from nijar_dti.schemas.iot import ObservacionIn


class MessageParseError(Exception):
    """Error de parseo o validación de un mensaje MQTT."""


@dataclass(frozen=True)
class ParsedMessage:
    """Mensaje MQTT parseado y normalizado."""

    topic: str
    sensor_slug: str  # último segmento útil del topic (informativo)
    observacion: ObservacionIn


# Topic esperado: nijar/sensors/<sensor_slug>/<measurement>
# Ejemplos:
#   nijar/sensors/smartoffice-01/co2
#   nijar/sensors/totem-rodalquilar/meteo
_SLUG_BLOQUEADOS = {"+", "#", "", "sensors"}


def parse_topic(topic: str) -> tuple[str, str]:
    """Extrae (sensor_slug, measurement) de un topic estándar.

    Acepta cualquier topic con al menos 4 segmentos. Lanza
    MessageParseError si el topic no cumple el patrón.
    """
    parts = [p for p in topic.split("/") if p]
    if len(parts) < 4 or parts[0] != "nijar" or parts[1] != "sensors":
        raise MessageParseError(f"Topic no esperado: {topic!r}")
    sensor_slug = parts[2]
    measurement = parts[3]
    if sensor_slug in _SLUG_BLOQUEADOS:
        raise MessageParseError(f"Slug de sensor inválido en topic: {topic!r}")
    return sensor_slug, measurement


def _decode_payload(payload: bytes | str) -> dict[str, Any]:
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MessageParseError(f"Payload no UTF-8: {exc}") from exc
    else:
        text = payload
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MessageParseError(f"Payload no es JSON válido: {exc}") from exc
    if not isinstance(data, dict):
        raise MessageParseError("Payload JSON debe ser un objeto")
    return data


def _normalizar_timestamp(value: Any) -> datetime:
    """Acepta varios formatos comunes y devuelve un datetime con tz."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        # epoch seconds o ms
        epoch = float(value)
        if epoch > 1e12:
            epoch /= 1000.0
        return datetime.fromtimestamp(epoch, tz=timezone.utc)
    if isinstance(value, str):
        # ISO 8601, con o sin "Z"
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MessageParseError(f"Timestamp inválido: {value!r}") from exc
    raise MessageParseError(f"Tipo de timestamp no soportado: {type(value).__name__}")


def parse_message(topic: str, payload: bytes | str) -> ParsedMessage:
    """Convierte (topic, payload) en una ``ObservacionIn`` validada.

    El payload aceptado puede tener dos formas:

    1. **Sensor con un único valor**::

           {
             "sensor_urn": "urn:ngsi-ld:Device:nijar:co2:smartoffice-01",  // opcional
             "valor": 845.2,
             "unidades": "ppm",
             "observado_en": "2026-05-15T10:23:45+02:00"
           }

    2. **Sensor con múltiples valores** (estación meteo, p. ej.)::

           {
             "valores": {"temperatura_c": 24.5, "humedad_porc": 62, ...},
             "observado_en": 1747299425
           }

    Si el payload no incluye ``sensor_urn`` se construye desde el topic.
    """
    sensor_slug, measurement = parse_topic(topic)
    data = _decode_payload(payload)

    sensor_urn = data.get("sensor_urn")
    if not sensor_urn:
        # urn:ngsi-ld:Device:nijar:<measurement>:<slug>
        sensor_urn = f"urn:ngsi-ld:Device:nijar:{measurement}:{sensor_slug}"

    observado_en = _normalizar_timestamp(data.get("observado_en"))

    valor_raw = data.get("valor")
    valor: float | None
    if valor_raw is None:
        valor = None
    else:
        try:
            valor = float(valor_raw)
        except (TypeError, ValueError) as exc:
            raise MessageParseError(f"Campo 'valor' no convertible a float: {valor_raw!r}") from exc

    valores = data.get("valores")
    if valores is not None and not isinstance(valores, dict):
        raise MessageParseError("Campo 'valores' debe ser un objeto JSON")

    if valor is None and valores is None:
        raise MessageParseError("El payload debe incluir 'valor' o 'valores'")

    try:
        observacion = ObservacionIn(
            sensor_urn=sensor_urn,
            observado_en=observado_en,
            valor=valor,
            valores=valores,
            unidades=data.get("unidades"),
            payload_original=data,
        )
    except ValidationError as exc:
        raise MessageParseError(f"Validación fallida: {exc}") from exc

    return ParsedMessage(topic=topic, sensor_slug=sensor_slug, observacion=observacion)
