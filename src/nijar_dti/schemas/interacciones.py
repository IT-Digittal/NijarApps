"""Esquemas de los listados de interacciones (chatbot y contenidos del tótem)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ------------------------------- Chatbot -------------------------------


class InteraccionChatbotOut(BaseModel):
    """Una pregunta del usuario y la respuesta del asistente."""

    id: UUID
    fecha: datetime
    canal: str
    totem: str | None = Field(None, description="Tótem de origen (si el canal es «totem»)")
    sesion_id: str
    idioma: str
    pregunta: str
    respuesta: str
    intent_detectado: str | None = None
    nivel_confianza: str
    score_confianza: float | None = None
    util: bool | None = None
    comentario: str | None = None
    latencia_ms: int | None = None
    fuentes: list[dict[str, Any]] | None = None
    demo: bool = Field(False, description="Registro de demostración (no real)")


class ResumenListadoChatbot(BaseModel):
    interacciones: int
    sesiones: int
    sin_respuesta: int = Field(..., description="Consultas fuera de dominio")
    utiles: int
    no_utiles: int
    latencia_media_ms: float | None = None


class ListadoChatbot(BaseModel):
    items: list[InteraccionChatbotOut]
    total: int
    page: int
    page_size: int
    resumen: ResumenListadoChatbot
    facetas: dict[str, dict[str, int]] = Field(
        default_factory=dict, description="Valores disponibles por filtro (con su recuento)"
    )


# ------------------------------- Tótem -------------------------------


class EventoTotemIn(BaseModel):
    """Una acción del visitante en el tótem (abrir sección, ficha, QR…)."""

    evento: str = Field(..., pattern=r"^[a-z_]{2,30}$")
    seccion: str | None = Field(None, max_length=40)
    contenido_id: str | None = Field(None, max_length=64)
    contenido: str | None = Field(None, max_length=200)
    detalle: str | None = Field(None, max_length=300)
    duracion_seg: int | None = Field(None, ge=0, le=86_400)
    ts: datetime | None = Field(
        None, description="Momento en el tótem (se acota a las últimas 24 h)"
    )


class EventosTotemIn(BaseModel):
    """Lote de eventos que el tótem envía cada pocos segundos (endpoint público)."""

    totem: str = Field(..., pattern=r"^[a-z0-9_-]{1,40}$")
    sesion_id: str = Field(..., min_length=4, max_length=100)
    idioma: str = Field("es", pattern=r"^(es|en|de|fr)$")
    eventos: list[EventoTotemIn] = Field(..., min_length=1, max_length=50)


class InteraccionTotemOut(BaseModel):
    id: UUID
    fecha: datetime
    totem: str | None = None
    sesion: str | None = None
    evento: str | None = None
    seccion: str | None = None
    contenido: str | None = None
    contenido_id: str | None = None
    detalle: str | None = None
    idioma: str | None = None
    duracion_seg: float | None = None
    demo: bool = False


class ContenidoTop(BaseModel):
    contenido: str
    seccion: str | None = None
    vistas: int


class ResumenListadoTotem(BaseModel):
    interacciones: int
    sesiones: int
    duracion_media_seg: float | None = None
    contenidos_top: list[ContenidoTop] = Field(default_factory=list)


class ListadoTotem(BaseModel):
    items: list[InteraccionTotemOut]
    total: int
    page: int
    page_size: int
    resumen: ResumenListadoTotem
    facetas: dict[str, dict[str, int]] = Field(default_factory=dict)
