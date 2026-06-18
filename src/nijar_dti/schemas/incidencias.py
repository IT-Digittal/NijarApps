"""Esquemas del módulo de incidencias / ticketing (C.1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidenciaIn(BaseModel):
    severidad: str = Field(..., pattern=r"^(critica|alta|media|baja)$")
    titulo: str = Field(..., max_length=255)
    componente: str = Field(..., max_length=60)
    descripcion: str | None = None
    detectada_en: datetime | None = None
    origen: str = Field("ticketing", pattern=r"^(monitorizacion|usuario|ticketing|preventivo)$")
    afecta_disponibilidad: bool = False
    es_preventiva: bool = False
    es_evento_seguridad: bool = False


class IncidenciaResolverIn(BaseModel):
    respondida_en: datetime | None = None
    resuelta_en: datetime | None = None
    incidente_confirmado: bool | None = None


class IncidenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    severidad: str
    titulo: str
    componente: str
    descripcion: str | None = None
    estado: str
    origen: str
    afecta_disponibilidad: bool
    es_preventiva: bool
    es_evento_seguridad: bool
    incidente_confirmado: bool
    detectada_en: datetime
    respondida_en: datetime | None = None
    resuelta_en: datetime | None = None


class CumplimientoANSSeveridad(BaseModel):
    severidad: str
    total: int = 0
    cumplen_resolucion: int = 0
    porcentaje_cumplimiento: float | None = None
    tiempo_medio_respuesta_h: float | None = None
    tiempo_medio_resolucion_h: float | None = None


class InformeANS(BaseModel):
    """Cumplimiento ANS agregado de un periodo."""

    desde: datetime
    hasta: datetime
    por_severidad: list[CumplimientoANSSeveridad] = Field(default_factory=list)
    incidencias_totales: int = 0
    sla_disponibilidad_porc: float = 99.0
