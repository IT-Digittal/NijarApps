"""Esquemas del gemelo digital: verticales externas (ThingsBoard)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EstadoGemelo(BaseModel):
    """Estado de configuración de las fuentes externas del gemelo."""

    thingsboard_configurado: bool


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
