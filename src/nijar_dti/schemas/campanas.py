"""Esquemas de campañas de promoción turística (bloque 9)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_ESTADOS = r"^(planificada|activa|finalizada|cancelada)$"
_OBJETIVOS = r"^(visitas|menciones|descargas|reservas|difusion|sensibilizacion)$"


class CampanaBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    fecha_inicio: datetime
    fecha_fin: datetime
    slug: str | None = Field(None, max_length=120)
    descripcion: str | None = None
    objetivo: str = Field("difusion", pattern=_OBJETIVOS)
    publico_objetivo: str | None = Field(None, max_length=255)
    canales: list[str] | None = None
    presupuesto: float | None = None
    landing_url: str | None = Field(None, max_length=500)
    recurso_id: UUID | None = None
    estado: str = Field("planificada", pattern=_ESTADOS)
    kpis_objetivo: dict | None = None
    resultados: dict | None = None
    etiquetas: list[str] | None = None
    metadata_adicional: dict | None = None


class CampanaIn(CampanaBase):
    """Alta de campaña."""


class CampanaUpdate(BaseModel):
    """Actualización parcial de campaña."""

    nombre: str | None = Field(None, max_length=255)
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    slug: str | None = Field(None, max_length=120)
    descripcion: str | None = None
    objetivo: str | None = Field(None, pattern=_OBJETIVOS)
    publico_objetivo: str | None = Field(None, max_length=255)
    canales: list[str] | None = None
    presupuesto: float | None = None
    landing_url: str | None = Field(None, max_length=500)
    recurso_id: UUID | None = None
    estado: str | None = Field(None, pattern=_ESTADOS)
    kpis_objetivo: dict | None = None
    resultados: dict | None = None
    etiquetas: list[str] | None = None
    metadata_adicional: dict | None = None


class CampanaOut(CampanaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class CampanaKPIs(BaseModel):
    """Eficacia medida de una campaña (cruce con menciones y visitas)."""

    campana_id: UUID
    slug: str | None = None
    nombre: str
    estado: str
    fecha_inicio: datetime
    fecha_fin: datetime

    # Menciones / social listening dentro de la ventana de campaña
    menciones: int = 0
    menciones_positivas: int = 0
    menciones_negativas: int = 0
    sentimiento_positivo_pct: float | None = None
    alcance_estimado: int = 0
    interacciones: int = 0

    # Visitas web/app durante la campaña
    visitas_web: int = 0
    visitas_app: int = 0

    # Comparativa con el periodo anterior de igual duración
    menciones_periodo_anterior: int = 0
    incremento_menciones_pct: float | None = None
    visitas_periodo_anterior: int = 0
    incremento_visitas_pct: float | None = None
