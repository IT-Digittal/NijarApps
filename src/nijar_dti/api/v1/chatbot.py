"""Endpoints REST del chatbot IA Asistente de Turismo de Níjar."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.chatbot import (
    ChatbotTelemetry,
    ChatQueryIn,
    ChatResponseOut,
    FeedbackIn,
    IntentInfo,
)
from nijar_dti.schemas.common import SerieDiaria
from nijar_dti.services import chatbot_rasa_adapter as svc

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
    ] = ...,
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
    ] = ...,
    db: AsyncSession = Depends(get_db),
) -> SerieDiaria:
    return await svc.telemetria_series(db, desde, hasta, granularidad)
