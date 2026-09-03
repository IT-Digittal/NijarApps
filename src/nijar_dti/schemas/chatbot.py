"""Esquemas chatbot IA."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatQueryIn(BaseModel):
    sesion_id: str = Field(..., max_length=100)
    canal: str = Field(..., pattern=r"^(web|app|totem)$")
    idioma: str = Field("es", pattern=r"^(es|en|de|fr)$")
    pregunta: str = Field(..., min_length=1, max_length=2000)
    contexto: dict | None = None


class TTSIn(BaseModel):
    """Petición de síntesis de voz de una respuesta del asistente."""

    texto: str = Field(..., min_length=1, max_length=800)
    idioma: str = Field("es", pattern=r"^(es|en|de|fr)$")
    canal: str = Field("totem", pattern=r"^(web|app|totem)$")


class FuenteRespuesta(BaseModel):
    tipo: str
    referencia: str
    descripcion: str | None = None
    fecha: str | None = None


class ChatResponseOut(BaseModel):
    interaccion_id: UUID
    respuesta: str
    intent_detectado: str | None = None
    nivel_confianza: str = Field(..., pattern=r"^(alta|media|fuera_de_dominio)$")
    score_confianza: float | None = None
    fuentes: list[FuenteRespuesta] | None = None
    sugerencias: list[str] | None = None
    latencia_ms: int


class FeedbackIn(BaseModel):
    sesion_id: str
    interaccion_id: UUID
    util: bool
    comentario: str | None = None


class IntentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    intent: str
    categoria: str
    pregunta_es: str
    nivel_confianza: str
    cobertura_idiomas: list[str] = Field(default_factory=list)


class TopIntentItem(BaseModel):
    nombre: str
    ocurrencias: int


class ChatbotTelemetry(BaseModel):
    desde: datetime | None = None
    hasta: datetime | None = None
    sesiones_totales: int
    sesiones_unicas: int
    interacciones_totales: int
    resolucion_autonoma_porc: float = Field(..., ge=0, le=100)
    satisfaccion_porc: float | None = None
    idiomas_distribucion: dict[str, float]
    top_intents: list[TopIntentItem]
