"""Esquemas del módulo de publicidad (empresas anunciantes)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from nijar_dti.models.empresa_anunciante import SECTORES_EMPRESA
from nijar_dti.schemas.common import I18nText

__all__ = ["SECTORES_EMPRESA", "EmpresaIn", "EmpresaOut", "EmpresaPublicaOut", "EmpresasPage"]


class EmpresaBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    sector: str = Field(..., max_length=30)
    descripcion: str | None = None
    descripcion_i18n: I18nText | None = None
    nucleo: str | None = Field(None, max_length=120)
    direccion: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=40)
    web: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    imagenes: list[str] | None = None
    latitud: float | None = None
    longitud: float | None = None
    destacado: bool = False
    prioridad: int = 0
    publicado: bool = False
    campana_desde: datetime | None = None
    campana_hasta: datetime | None = None


class EmpresaIn(EmpresaBase):
    pass


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class EmpresaPublicaOut(BaseModel):
    """Empresa tal como la consume el tótem (sin datos de gestión)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    sector: str
    descripcion: str | None
    descripcion_i18n: I18nText | None
    nucleo: str | None
    direccion: str | None
    telefono: str | None
    web: str | None
    imagenes: list[str] | None
    destacado: bool


class EmpresasPage(BaseModel):
    items: list[EmpresaOut]
    total: int


class EventoMetricaIn(BaseModel):
    """Un evento de visibilidad registrado por el tótem (anónimo)."""

    empresa_id: UUID
    tipo: Literal["impresion", "toque"]
    n: int = Field(1, ge=1, le=100)


class LoteMetricasIn(BaseModel):
    eventos: list[EventoMetricaIn] = Field(..., max_length=200)


class MetricaEmpresaOut(BaseModel):
    """Totales de visibilidad de un anunciante en el periodo consultado."""

    empresa_id: UUID
    impresiones: int
    toques: int


class ResumenMetricasOut(BaseModel):
    dias: int
    metricas: list[MetricaEmpresaOut]
