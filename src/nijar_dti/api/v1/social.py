"""Endpoints de Social Listening / Big Data turístico."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.common import PageParams, Paginated
from nijar_dti.schemas.social import (
    OpinionOut,
    SentimentSeries,
    ShareOfVoice,
    TopicItem,
)
from nijar_dti.services import social_service as svc

router = APIRouter()


def _page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def _opinion_to_out(o) -> OpinionOut:
    return OpinionOut(
        id=o.id,
        fuente=o.fuente,
        fuente_id_externo=o.fuente_id_externo,
        autor_handle=o.autor_handle,
        texto_original=o.texto_original,
        idioma=o.idioma,
        publicado_en=o.publicado_en,
        sentimiento=o.sentimiento,
        score_sentimiento=float(o.score_sentimiento) if o.score_sentimiento is not None else None,
        temas=o.temas,
        entidades_mencionadas=o.entidades_mencionadas,
        metricas=o.metricas,
    )


@router.get(
    "/mentions",
    response_model=Paginated[OpinionOut],
    summary="Menciones del destino capturadas en RRSS",
)
async def list_mentions(
    fuente: str | None = Query(None),
    sentimiento: str | None = Query(None, pattern=r"^(positivo|neutro|negativo)$"),
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Paginated[OpinionOut]:
    rows, total = await svc.listar_menciones(
        db, fuente, sentimiento, desde, hasta, page
    )
    items = [_opinion_to_out(o) for o in rows]
    return Paginated[OpinionOut].build(items, total, page)


@router.get(
    "/kpis/sentiment",
    response_model=SentimentSeries,
    summary="KPI de sentimiento del destino (serie temporal)",
)
async def kpi_sentimiento(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    granularidad: str = Query("dia", pattern=r"^(hora|dia|semana|mes)$"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> SentimentSeries:
    return await svc.serie_sentimiento(db, desde, hasta, granularidad)


@router.get(
    "/kpis/share-of-voice",
    response_model=list[ShareOfVoice],
    summary="Share of voice por plataforma",
)
async def kpi_share_of_voice(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ShareOfVoice]:
    return await svc.share_of_voice(db, desde, hasta)


@router.get(
    "/topics",
    response_model=list[TopicItem],
    summary="Top temas mencionados",
)
async def topics(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[TopicItem]:
    return await svc.top_topics(db, desde, hasta, limit)
