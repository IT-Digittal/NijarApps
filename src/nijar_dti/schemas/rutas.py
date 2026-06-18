"""Esquemas del planificador de rutas y recomendaciones (A.1 / B.2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlanificarRutaIn(BaseModel):
    """Petición de planificación de un itinerario turístico."""

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    categorias: list[str] | None = Field(
        default=None, description="Filtra por categorías de recurso (playa, ruta, mirador…)"
    )
    max_paradas: int = Field(5, ge=1, le=20)
    modo: str = Field("bici", pattern=r"^(a_pie|bici|coche)$")
    idioma: str = Field("es", pattern=r"^(es|en|de|fr)$")


class ParadaOut(BaseModel):
    orden: int
    id: UUID
    nombre: str
    categoria: str
    lat: float
    lon: float
    distancia_desde_anterior_m: float
    distancia_acumulada_m: float


class RutaPlanificada(BaseModel):
    origen: dict[str, float]
    modo: str
    paradas: list[ParadaOut] = Field(default_factory=list)
    distancia_total_m: float = 0.0
    duracion_desplazamiento_min: int = 0
    mensaje: str | None = None


class RecursoSugerido(BaseModel):
    id: UUID
    nombre: str
    categoria: str
    motivo: str


class EventoSugerido(BaseModel):
    id: UUID
    nombre: str
    tipo: str
    fecha_inicio: datetime
    fecha_fin: datetime
    direccion: str | None = None


class RecomendacionesOut(BaseModel):
    """Propuesta de visitas y de asistencia a eventos."""

    fecha_referencia: datetime
    idioma: str
    eventos: list[EventoSugerido] = Field(default_factory=list)
    recursos: list[RecursoSugerido] = Field(default_factory=list)
    mensaje: str | None = None
