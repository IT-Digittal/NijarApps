"""Endpoints REST del chatbot IA Asistente de Turismo de Níjar."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.config import get_settings
from nijar_dti.core.database import get_db
from nijar_dti.core.export import csv_response
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
from nijar_dti.schemas.interacciones import InteraccionChatbotOut, ListadoChatbot
from nijar_dti.services import chatbot_rasa_adapter as svc
from nijar_dti.services import chatbot_tts_service as tts_svc
from nijar_dti.services import consumo_ia_service
from nijar_dti.services import interacciones_service as inter_svc

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


# ----------------------- Listado de interacciones (panel) -----------------------

# Las conversaciones son texto libre del visitante: solo perfiles de gestión y auditoría
_ver_conversaciones = require_roles(
    "administrador_tic", "analista_datos", "gestor_contenidos", "auditor"
)


def _filtros_listado(
    desde: datetime | None = Query(None, description="Desde (fecha u hora)"),
    hasta: datetime | None = Query(None, description="Hasta (una fecha sin hora incluye el día)"),
    canal: str | None = Query(None, pattern=r"^(web|app|totem)$"),
    totem: str | None = Query(None, pattern=r"^[a-z0-9_-]{1,40}$"),
    idioma: str | None = Query(None, pattern=r"^(es|en|de|fr)$"),
    intent: str | None = Query(None, max_length=100),
    nivel: str | None = Query(None, pattern=r"^(alta|media|fuera_de_dominio)$"),
    util: str | None = Query(None, pattern=r"^(si|no|sin)$", description="Valoración"),
    q: str | None = Query(None, max_length=200, description="Texto en pregunta o respuesta"),
    sesion: str | None = Query(None, max_length=100),
    incluir_demo: bool = Query(False, description="Incluir los registros de demostración"),
) -> dict[str, object]:
    return {
        "desde": desde,
        "hasta": hasta,
        "canal": canal,
        "totem": totem,
        "idioma": idioma,
        "intent": intent,
        "nivel": nivel,
        "util": util,
        "q": q,
        "sesion": sesion,
        "incluir_demo": incluir_demo,
    }


_ORDEN = Query("reciente", pattern=r"^(reciente|antiguo|latencia|confianza)$")


@router.get(
    "/interacciones",
    response_model=ListadoChatbot,
    summary="Listado de preguntas y respuestas del asistente (con filtros)",
)
async def listar_interacciones(
    filtros: Annotated[dict[str, object], Depends(_filtros_listado)],
    user: Annotated[CurrentUser, Depends(_ver_conversaciones)],
    page: int = Query(1, ge=1, le=100_000),
    page_size: int = Query(50, ge=1, le=200),
    orden: str = _ORDEN,
    db: AsyncSession = Depends(get_db),
) -> ListadoChatbot:
    return await inter_svc.listar_chatbot(
        db, page=page, page_size=page_size, orden=orden, **filtros
    )


@router.get(
    "/interacciones/export",
    summary="Exportar las interacciones filtradas a CSV (Excel)",
    response_class=Response,
)
async def exportar_interacciones(
    filtros: Annotated[dict[str, object], Depends(_filtros_listado)],
    user: Annotated[CurrentUser, Depends(_ver_conversaciones)],
    orden: str = _ORDEN,
    db: AsyncSession = Depends(get_db),
) -> Response:
    filas = await inter_svc.exportar_chatbot(db, orden=orden, **filtros)
    hoy = datetime.now(UTC).strftime("%Y%m%d")
    return csv_response(filas, f"interacciones_chatbot_{hoy}", excel=True)


@router.get(
    "/interacciones/sesion/{sesion_id}",
    response_model=list[InteraccionChatbotOut],
    summary="Conversación completa de una sesión",
)
async def conversacion_sesion(
    sesion_id: str,
    user: Annotated[CurrentUser, Depends(_ver_conversaciones)],
    db: AsyncSession = Depends(get_db),
) -> list[InteraccionChatbotOut]:
    return await inter_svc.conversacion(db, sesion_id)
