"""Esquemas del gemelo digital: verticales externas (ThingsBoard)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EstadoGemelo(BaseModel):
    """Estado de configuración de las fuentes externas del gemelo."""

    thingsboard_configurado: bool
    bettair_configurado: bool = False


class BanderaPlayaOut(BaseModel):
    nombre: str
    estado: str  # verde | amarilla | roja | sin_bandera | desconocido
    latitud: float
    longitud: float


class BanderasPlayasOut(BaseModel):
    fuente: str = "thingsboard"
    obtenido_en: datetime
    total: int
    banderas: list[BanderaPlayaOut]


class EstacionAireOut(BaseModel):
    """Estación Bettair de calidad del aire y meteorología."""

    id: str
    latitud: float
    longitud: float
    estado: str  # active | inactive | desconocido
    bateria_pct: float | None
    ultima_conexion: datetime | None
    medido_en: datetime | None
    eaqi: int | None  # índice europeo de calidad del aire (1 buena … 6 extrema)
    eaqi_texto: str | None
    temperatura_c: float | None
    humedad_pct: float | None
    presion_hpa: float | None
    no2_ugm3: float | None
    o3_ugm3: float | None
    pm25_ugm3: float | None
    pm10_ugm3: float | None


class EstacionesAireOut(BaseModel):
    fuente: str = "bettair"
    obtenido_en: datetime
    total: int
    estaciones: list[EstacionAireOut]


class AforoParqueOut(BaseModel):
    """Aforo en tiempo real del P.N. Cabo de Gata (conteo de accesos)."""

    fuente: str = "thingsboard"
    obtenido_en: datetime
    medido_en: datetime | None  # marca temporal de la última muestra en origen
    aforo_actual: int | None  # vehículos dentro ahora
    entradas_hoy: int | None
    salidas_hoy: int | None
    total_vehiculos: int | None
    total_motorizados: int | None
    total_no_motorizados: int | None
    total_personas: int | None
