"""Esquemas del módulo de contexto histórico (backfill de fuentes públicas)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContextoRecordIn(BaseModel):
    """Registro de contexto a ingestar (idempotente por clave natural)."""

    fuente: str
    indicador: str
    periodo: str = Field(..., description="AAAA-MM | AAAA-Qn | AAAA")
    valor: float
    unidad: str | None = None
    ambito: str = "provincia_almeria"
    metadatos: dict | None = None


class ContextoIngestIn(BaseModel):
    """Cuerpo del endpoint de ingesta masiva de backfill."""

    registros: list[ContextoRecordIn]


class ContextoIngestResult(BaseModel):
    """Resultado de una ingesta idempotente."""

    recibidos: int
    insertados: int
    actualizados: int
    omitidos: int = 0


class ContextoPunto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    periodo: str
    valor: float
    unidad: str | None = None
    ambito: str


class ContextoSerie(BaseModel):
    fuente: str
    indicador: str
    puntos: list[ContextoPunto]


class FactorExpansionOut(BaseModel):
    factor: float
    cobertura_estimada_pct: float
    metodo: str
    muestra_referencia: int | None = None
    visitantes_oficiales_estimados: float | None = None
    es_preliminar: bool = False
    periodo_referencia: str | None = None
    calculado_en: datetime | None = None


class ContextoRegistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fuente: str
    indicador: str
    periodo: str
    valor: float
    unidad: str | None = None
    ambito: str
