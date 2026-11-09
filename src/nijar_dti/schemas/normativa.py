"""Esquemas de la normativa municipal (ordenanzas de la sede electrónica)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NormativaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    tipo: str
    nombre_archivo: str
    tamano_bytes: int
    paginas: int
    url_origen: str | None = None
    fecha_publicacion: date | None = None
    created_at: datetime
    sin_texto: bool = False
    extracto: str | None = None  # pasaje con las palabras buscadas resaltadas
    relevancia: float | None = None


class FragmentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    orden: int
    articulo: str | None = None
    texto: str


class NormativaDetalle(NormativaOut):
    fragmentos: list[FragmentoOut] = []


class ResumenNormativa(BaseModel):
    total: int
    por_tipo: dict[str, int]
    sin_texto: int
    ultima_importacion: datetime | None = None


class ImportacionNormativaOut(BaseModel):
    importadas: int
    actualizadas: int
    errores: list[str]
    documentos: list[NormativaOut]


class PasajeOut(BaseModel):
    normativa_id: UUID
    titulo: str
    articulo: str | None = None
    texto: str
    relevancia: float
    url_pdf: str
