"""Esquemas de documentos adjuntos a puntos del territorio."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# Capas del gemelo que admiten documentos (cualquier identificador dentro de ellas)
TIPOS_ENTIDAD_VALIDOS = {
    "recurso",
    "sensor",
    "cuadro",
    "contenedor",
    "movilidad",
    "camara",
    "bandera",
    "estacion_aire",
    "otro",
}

TAMANO_MAX_BYTES = 25 * 1024 * 1024  # 25 MB por documento


class DocumentoPuntoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entidad_tipo: str
    entidad_id: str
    entidad_nombre: str
    latitud: float | None
    longitud: float | None
    nombre_archivo: str
    descripcion: str | None
    tipo_mime: str
    tamano_bytes: int
    subido_por: str | None
    created_at: datetime


class DocumentosPage(BaseModel):
    items: list[DocumentoPuntoOut]
    total: int
