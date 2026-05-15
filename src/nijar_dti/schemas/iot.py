"""Esquemas IoT (sensores y observaciones)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from nijar_dti.schemas.common import GeoPoint


class SensorBase(BaseModel):
    urn: str = Field(..., pattern=r"^urn:ngsi-ld:Device:nijar:[a-z0-9-]+:[a-z0-9-]+$")
    nombre: str
    tipo: str
    fabricante: str | None = None
    modelo: str | None = None
    descripcion_ubicacion: str | None = None
    unidades_medida: str | None = None
    rango_minimo: float | None = None
    rango_maximo: float | None = None
    umbrales_alerta: dict | None = None
    frecuencia_muestreo_seg: int | None = None
    estado: str = "desconocido"
    topic_mqtt: str | None = None
    activo: bool = True


class SensorIn(SensorBase):
    ubicacion: GeoPoint | None = None


class SensorOut(SensorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ubicacion: GeoPoint | None = None
    nivel_bateria: float | None = None
    created_at: datetime
    updated_at: datetime


class ObservacionIn(BaseModel):
    sensor_urn: str = Field(..., pattern=r"^urn:ngsi-ld:Device:nijar:[a-z0-9-]+:[a-z0-9-]+$")
    observado_en: datetime
    valor: float | None = None
    valores: dict | None = None
    unidades: str | None = None
    payload_original: dict | None = None


class ObservacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sensor_id: UUID
    observado_en: datetime
    valor: float | None = None
    valores: dict | None = None
    unidades: str | None = None
    valido: bool
    motivo_invalidez: str | None = None


class IngestResponse(BaseModel):
    observacion_id: UUID
    valido: bool
    motivo_invalidez: str | None = None
