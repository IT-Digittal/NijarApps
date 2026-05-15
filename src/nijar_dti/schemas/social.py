"""Esquemas Social Listening / Big Data."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OpinionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fuente: str
    fuente_id_externo: str | None = None
    autor_handle: str | None = None
    texto_original: str
    idioma: str | None = None
    publicado_en: datetime
    sentimiento: str
    score_sentimiento: float | None = None
    temas: list[str] | None = None
    entidades_mencionadas: list[str] | None = None
    metricas: dict | None = None


class SentimentPoint(BaseModel):
    timestamp: datetime
    positivo: int = 0
    neutro: int = 0
    negativo: int = 0
    score_medio: float | None = None


class SentimentSeries(BaseModel):
    granularidad: str
    desde: datetime | None = None
    hasta: datetime | None = None
    puntos: list[SentimentPoint]


class TopicItem(BaseModel):
    tema: str
    menciones: int
    sentimiento_medio: float | None = None


class ShareOfVoice(BaseModel):
    fuente: str
    porcentaje: float = Field(..., ge=0, le=100)
    menciones: int
