"""Esquemas del Cuadro de Mando de Dirección (perfil ejecutivo/político).

Vista resumida y estratégica: estado global, semáforo por vertical, alertas
relevantes, recomendaciones e impacto. Los indicadores económicos y
ambientales llevan ``estimado=True`` cuando se derivan de factores (no de un
dato medido directamente).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Estado = Literal["verde", "ambar", "rojo"]
Riesgo = Literal["bajo", "medio", "alto"]
Nivel = Literal["bajo", "medio", "alto", "critico"]
Prioridad = Literal["critica", "alta", "media", "informativa"]
EstadoRecomendacion = Literal["pendiente", "en_revision", "aceptada", "descartada", "ejecutada"]


class EstadoVertical(BaseModel):
    """Semáforo de una vertical con su indicador clave y recomendación."""

    clave: str
    nombre: str
    icono: str
    estado: Estado
    indicador_clave: str
    riesgo: Riesgo
    recomendacion: str


class AlertaDireccion(BaseModel):
    """Alerta relevante para la toma de decisiones (no técnica)."""

    nivel: Nivel
    area: str
    motivo: str
    impacto: str
    recomendacion: str


class RecomendacionIA(BaseModel):
    """Recomendación redactada para dirección."""

    clave: str = ""
    titulo: str
    area: str
    justificacion: str
    impacto: str
    prioridad: Prioridad
    accion: str
    motor: str = "reglas"  # "reglas" | "openai" (conmutador mixto)
    estado: EstadoRecomendacion = "pendiente"
    comentario: str | None = None


class EstadoRecomendacionUpdate(BaseModel):
    """Payload para cambiar el estado / comentario de una recomendación."""

    estado: EstadoRecomendacion | None = None
    comentario: str | None = Field(default=None, max_length=500)


class ImpactoEconomico(BaseModel):
    ahorro_estimado_eur_mes: float
    coste_energetico_mes_eur: float
    estimado: bool = True


class ImpactoCiudadano(BaseModel):
    satisfaccion_pct: float | None = None
    nps: float | None = None
    sentimiento_medio: float | None = None
    menciones_mes: int = 0


class ImpactoAmbiental(BaseModel):
    co2_evitado_t_anio: float
    autoconsumo_pct: float
    consumo_energetico_kwh_mes: float
    estimado: bool = True


class ImpactoDireccion(BaseModel):
    economico: ImpactoEconomico
    ciudadano: ImpactoCiudadano
    ambiental: ImpactoAmbiental


class KpiInteranual(BaseModel):
    """Indicador con comparativa "vs mismo periodo del año pasado".

    Solo se produce cuando existe serie histórica real (turismo: contexto
    oficial INE/Junta/AENA). No hay interanual para las verticales técnicas.
    """

    clave: str
    nombre: str
    fuente: str
    vertical: str | None = None
    periodo: str
    periodo_anterior: str
    valor: float
    valor_anterior: float
    variacion_pct: float
    unidad: str | None = None
    tendencia: Literal["sube", "baja", "estable"] = "estable"
    # Semántica para colorear: si "subir" o "bajar" es lo positivo.
    sentido: Literal["subir_bueno", "bajar_bueno", "neutro"] = "subir_bueno"


class ResumenMunicipal(BaseModel):
    """Cockpit ejecutivo del municipio."""

    estado_global: int = Field(..., ge=0, le=100)
    estado_texto: Literal["correcto", "atencion", "critico"]
    servicios_ok: int
    servicios_total: int
    areas_alerta: list[str]
    incidencias_criticas: int
    disponibilidad_media_pct: float
    satisfaccion_pct: float | None = None
    ahorro_estimado_eur_mes: float
    co2_evitado_t_anio: float
    semaforo: list[EstadoVertical]
    alertas: list[AlertaDireccion]
    impacto: ImpactoDireccion
    interanual_turismo: list[KpiInteranual] = Field(default_factory=list)
    interanual_verticales: list[KpiInteranual] = Field(default_factory=list)
    generado_en: datetime
