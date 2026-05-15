"""Entidad Sensor — Catálogo de sensores IoT del destino.

Compatible con FIWARE Smart Data Model `Device`.
Representa los sensores ambientales del Smart Office, las estaciones
meteorológicas, los beacons BLE y otros dispositivos IoT integrados.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class TipoSensor(StrEnum):
    """Tipologías de sensor."""

    AMBIENTAL_CO2 = "ambiental_co2"
    AMBIENTAL_TEMPERATURA = "ambiental_temperatura"
    AMBIENTAL_HUMEDAD = "ambiental_humedad"
    AMBIENTAL_RUIDO = "ambiental_ruido"
    METEO = "meteo"
    AFORO = "aforo"
    BEACON_BLE = "beacon_ble"
    WIFI_PUBLICO = "wifi_publico"
    VIDEOCAMARA = "videocamara"
    ALUMBRADO = "alumbrado"
    OTRO = "otro"


class EstadoSensor(StrEnum):
    """Estado operativo del sensor."""

    OPERATIVO = "operativo"
    OFFLINE = "offline"
    MANTENIMIENTO = "mantenimiento"
    AVERIA = "averia"
    BATERIA_BAJA = "bateria_baja"
    DESCONOCIDO = "desconocido"


class Sensor(Base, AuditMixin):
    """Catálogo de dispositivos IoT integrados en la plataforma DTI."""

    __tablename__ = "sensores"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # URN único del sensor (FIWARE)
    # Formato: urn:ngsi-ld:Device:nijar:<tipo>:<id>
    urn: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    nombre: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[TipoSensor] = mapped_column(String(50), index=True)

    # Datos del fabricante / modelo
    fabricante: Mapped[str | None] = mapped_column(String(100), default=None)
    modelo: Mapped[str | None] = mapped_column(String(100), default=None)
    numero_serie: Mapped[str | None] = mapped_column(String(100), default=None)
    firmware_version: Mapped[str | None] = mapped_column(String(50), default=None)

    # Ubicación del sensor
    ubicacion: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        default=None,
    )
    descripcion_ubicacion: Mapped[str | None] = mapped_column(Text, default=None)

    # Configuración técnica
    unidades_medida: Mapped[str | None] = mapped_column(String(50), default=None)
    rango_minimo: Mapped[float | None] = mapped_column(default=None)
    rango_maximo: Mapped[float | None] = mapped_column(default=None)
    umbrales_alerta: Mapped[dict | None] = mapped_column(JSON, default=None)
    frecuencia_muestreo_seg: Mapped[int | None] = mapped_column(default=None)

    # Estado operativo (cacheado del último heartbeat)
    estado: Mapped[EstadoSensor] = mapped_column(
        String(30), default=EstadoSensor.DESCONOCIDO, index=True
    )
    nivel_bateria: Mapped[float | None] = mapped_column(default=None)

    # Topic MQTT al que publica
    topic_mqtt: Mapped[str | None] = mapped_column(String(255), default=None)

    # Calibración
    fecha_ultima_calibracion: Mapped[str | None] = mapped_column(String(20), default=None)
    fecha_proxima_calibracion: Mapped[str | None] = mapped_column(String(20), default=None)

    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    activo: Mapped[bool] = mapped_column(default=True)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_sensores_tipo_estado", "tipo", "estado"),
        Index("ix_sensores_ubicacion_gist", "ubicacion", postgresql_using="gist"),
    )
