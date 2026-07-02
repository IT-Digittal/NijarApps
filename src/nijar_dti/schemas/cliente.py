"""Esquemas de la ficha general del cliente / Ayuntamiento (bloque 1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClienteBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    area_responsable: str | None = Field(None, max_length=255)
    proyecto: str | None = Field(None, max_length=255)
    descripcion: str | None = None
    cif: str | None = Field(None, max_length=20)
    direccion: str | None = Field(None, max_length=500)
    municipio: str = Field("Níjar", max_length=100)
    provincia: str = Field("Almería", max_length=100)
    responsable_municipal: dict | None = None
    responsables_tecnicos: list[dict] | None = None
    canales_oficiales: dict | None = None
    idiomas_activos: list[str] | None = None
    fecha_inicio_explotacion: datetime | None = None
    fecha_fin_mantenimiento: datetime | None = None
    hitos: list[dict] | None = None
    metadata_adicional: dict | None = None


class ClienteIn(ClienteBase):
    """Alta o reemplazo completo de la ficha del cliente."""


class ClienteUpdate(BaseModel):
    """Actualización parcial de la ficha del cliente."""

    nombre: str | None = Field(None, max_length=255)
    area_responsable: str | None = Field(None, max_length=255)
    proyecto: str | None = Field(None, max_length=255)
    descripcion: str | None = None
    cif: str | None = Field(None, max_length=20)
    direccion: str | None = Field(None, max_length=500)
    municipio: str | None = Field(None, max_length=100)
    provincia: str | None = Field(None, max_length=100)
    responsable_municipal: dict | None = None
    responsables_tecnicos: list[dict] | None = None
    canales_oficiales: dict | None = None
    idiomas_activos: list[str] | None = None
    fecha_inicio_explotacion: datetime | None = None
    fecha_fin_mantenimiento: datetime | None = None
    hitos: list[dict] | None = None
    metadata_adicional: dict | None = None
    activo: bool | None = None


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime
