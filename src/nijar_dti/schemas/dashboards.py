"""Esquemas dashboards (Smart Office, Big Data, informe mensual)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SmartOfficeOverview(BaseModel):
    """KPIs en tiempo real del Smart Office."""

    sensores_total: int
    sensores_operativos: int
    sensores_offline: int
    alertas_activas: int
    co2_actual_ppm: float | None = None
    temperatura_actual_c: float | None = None
    humedad_actual_porc: float | None = None
    ruido_actual_db: float | None = None
    timestamp: datetime


class EnvironmentPoint(BaseModel):
    timestamp: datetime
    co2_ppm: float | None = None
    temperatura_c: float | None = None
    humedad_porc: float | None = None
    ruido_db: float | None = None


class EnvironmentSeries(BaseModel):
    granularidad: str
    desde: datetime | None = None
    hasta: datetime | None = None
    puntos: list[EnvironmentPoint]


class BigDataOverview(BaseModel):
    menciones_total: int
    menciones_ultimo_mes: int
    sentimiento_medio: float | None = None
    fuentes_activas: int
    temas_top: list[str]


class TotemUsageStats(BaseModel):
    desde: datetime | None = None
    hasta: datetime | None = None
    interacciones_total: int
    sesiones_unicas: int
    duracion_media_seg: float | None = None
    secciones_top: list[dict]


class TotemHealth(BaseModel):
    """Salud/telemetría de un tótem (bloque 7 del pliego)."""

    urn: str
    nombre: str
    estado: str
    disponibilidad_pct: float | None = None
    temperatura_interna_media: float | None = None
    temperatura_interna_max: float | None = None
    reinicios: int = 0
    conectividad_media_pct: float | None = None
    ultima_comunicacion: datetime | None = None
    muestras: int = 0


class TotemsHealthOverview(BaseModel):
    """Disponibilidad agregada y salud por tótem."""

    disponibilidad_media_pct: float | None = None
    totems: list[TotemHealth]


class MonthlyReport(BaseModel):
    """Datos del informe mensual de servicio (C.1)."""

    year: int = Field(..., ge=2025, le=2100)
    month: int = Field(..., ge=1, le=12)

    disponibilidad_por_componente: dict[str, float]

    interacciones_totems: int
    sesiones_chatbot: int
    visitas_web_estimadas: int

    incidencias_criticas: int
    incidencias_altas: int
    incidencias_resueltas: int

    eventos_seguridad: int
    incidentes_confirmados: int

    acciones_preventivas_ejecutadas: int

    sentimiento_medio: float | None = None
    menciones_periodo: int = 0

    # Eficacia digital (alimentada por GA4)
    eficacia_digital: dict | None = None
