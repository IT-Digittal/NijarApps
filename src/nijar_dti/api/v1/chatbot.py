"""Endpoints REST del chatbot IA Asistente de Turismo de Níjar."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.config import get_settings
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.chatbot import (
    ChatbotTelemetry,
    ChatQueryIn,
    ChatResponseOut,
    FeedbackIn,
    IntentInfo,
    TTSIn,
)
from nijar_dti.schemas.common import SerieDiaria
from nijar_dti.services import chatbot_rasa_adapter as svc
from nijar_dti.services import chatbot_tts_service as tts_svc
from nijar_dti.services import consumo_ia_service

router = APIRouter()


@router.post(
    "/query",
    response_model=ChatResponseOut,
    summary="Consultar al asistente de turismo",
)
async def query(payload: ChatQueryIn, db: AsyncSession = Depends(get_db)) -> ChatResponseOut:
    """Endpoint público — accesible sin autenticación desde web/app/tótems."""
    return await svc.consultar(db, payload)


@router.post(
    "/tts",
    summary="Sintetizar una respuesta del asistente con voz natural",
    response_class=Response,
)
async def tts(payload: TTSIn, db: AsyncSession = Depends(get_db)) -> Response:
    """Endpoint público: lo usa el tótem para leer las respuestas en voz alta.

    Devuelve MP3 con voz neuronal (OpenAI TTS, misma clave que el motor
    generativo). Si la clave no está configurada responde 503 y el tótem
    degrada a la voz del navegador. Los audios se cachean por frase.
    """
    if not tts_svc.tts_configurado():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Síntesis de voz sin configurar (OPENAI_API_KEY)",
        )
    inicio = datetime.now(UTC)
    try:
        audio = await tts_svc.sintetizar(payload.texto, payload.idioma)
    except tts_svc.TTSNoDisponibleError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except tts_svc.TTSError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    await consumo_ia_service.registrar(
        db,
        modelo=get_settings().openai_tts_model,
        servicio="chatbot_tts",
        canal=payload.canal,
        idioma=payload.idioma,
        tokens_entrada=max(len(payload.texto) // 4, 1),  # aproximación de tokens de texto
        latencia_ms=int((datetime.now(UTC) - inicio).total_seconds() * 1000),
    )
    return Response(content=audio, media_type="audio/mpeg")


@router.post(
    "/feedback",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registrar feedback de una interacción",
)
async def feedback(payload: FeedbackIn, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await svc.registrar_feedback(db, payload.interaccion_id, payload.util, payload.comentario)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/intents",
    response_model=list[IntentInfo],
    summary="Listar intents configurados (admin)",
)
async def intents(
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> list[IntentInfo]:
    return await svc.listar_intents(db)


@router.get(
    "/telemetry",
    response_model=ChatbotTelemetry,
    summary="Telemetría agregada del chatbot",
)
async def telemetry(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "analista_datos"))
    ] = ...,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
) -> ChatbotTelemetry:
    return await svc.telemetria(db, desde, hasta)


@router.get(
    "/telemetry/series",
    response_model=SerieDiaria,
    summary="Serie diaria de interacciones del chatbot",
)
async def telemetry_series(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    granularidad: str = Query("dia", pattern=r"^dia$"),
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "analista_datos"))
    ] = ...,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
) -> SerieDiaria:
    return await svc.telemetria_series(db, desde, hasta, granularidad)
