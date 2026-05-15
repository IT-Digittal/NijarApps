"""Lógica de negocio para Social Listening / Big Data turístico."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.opinion import Opinion
from nijar_dti.schemas.common import PageParams
from nijar_dti.schemas.social import (
    SentimentPoint,
    SentimentSeries,
    ShareOfVoice,
    TopicItem,
)


_GRANULARIDADES = {
    "hora": "hour",
    "dia": "day",
    "semana": "week",
    "mes": "month",
}


async def listar_menciones(
    db: AsyncSession,
    fuente: str | None,
    sentimiento: str | None,
    desde: datetime | None,
    hasta: datetime | None,
    page: PageParams,
) -> tuple[list[Opinion], int]:
    base = select(Opinion)
    if fuente:
        base = base.where(Opinion.fuente == fuente)
    if sentimiento:
        base = base.where(Opinion.sentimiento == sentimiento)
    if desde:
        base = base.where(Opinion.publicado_en >= desde)
    if hasta:
        base = base.where(Opinion.publicado_en <= hasta)

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )
    res = await db.execute(
        base.order_by(Opinion.publicado_en.desc()).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


async def serie_sentimiento(
    db: AsyncSession,
    desde: datetime | None,
    hasta: datetime | None,
    granularidad: str = "dia",
) -> SentimentSeries:
    if granularidad not in _GRANULARIDADES:
        granularidad = "dia"
    pg_unit = _GRANULARIDADES[granularidad]

    bucket = func.date_trunc(pg_unit, Opinion.publicado_en).label("bucket")
    q = select(
        bucket,
        func.count(case((Opinion.sentimiento == "positivo", 1))).label("positivos"),
        func.count(case((Opinion.sentimiento == "neutro", 1))).label("neutros"),
        func.count(case((Opinion.sentimiento == "negativo", 1))).label("negativos"),
        func.avg(Opinion.score_sentimiento).label("score_medio"),
    )
    if desde:
        q = q.where(Opinion.publicado_en >= desde)
    if hasta:
        q = q.where(Opinion.publicado_en <= hasta)
    q = q.group_by(bucket).order_by(bucket)

    rows = (await db.execute(q)).all()
    puntos = [
        SentimentPoint(
            timestamp=row.bucket,
            positivo=int(row.positivos or 0),
            neutro=int(row.neutros or 0),
            negativo=int(row.negativos or 0),
            score_medio=float(row.score_medio) if row.score_medio is not None else None,
        )
        for row in rows
    ]
    return SentimentSeries(
        granularidad=granularidad, desde=desde, hasta=hasta, puntos=puntos
    )


async def share_of_voice(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> list[ShareOfVoice]:
    q = select(Opinion.fuente, func.count(Opinion.id).label("n"))
    if desde:
        q = q.where(Opinion.publicado_en >= desde)
    if hasta:
        q = q.where(Opinion.publicado_en <= hasta)
    q = q.group_by(Opinion.fuente)
    rows = (await db.execute(q)).all()
    total = sum(int(r.n) for r in rows) or 1
    return [
        ShareOfVoice(
            fuente=r.fuente,
            menciones=int(r.n),
            porcentaje=round(int(r.n) * 100 / total, 2),
        )
        for r in rows
    ]


async def top_topics(
    db: AsyncSession,
    desde: datetime | None,
    hasta: datetime | None,
    limit: int = 20,
) -> list[TopicItem]:
    """Calcula los temas más mencionados (sobre el array `temas`)."""
    q = select(Opinion.temas, Opinion.score_sentimiento)
    if desde:
        q = q.where(Opinion.publicado_en >= desde)
    if hasta:
        q = q.where(Opinion.publicado_en <= hasta)
    rows = (await db.execute(q)).all()

    counter: Counter[str] = Counter()
    score_por_tema: dict[str, list[float]] = {}
    for row in rows:
        if not row.temas:
            continue
        for tema in row.temas:
            counter[tema] += 1
            if row.score_sentimiento is not None:
                score_por_tema.setdefault(tema, []).append(float(row.score_sentimiento))

    out: list[TopicItem] = []
    for tema, n in counter.most_common(limit):
        scores = score_por_tema.get(tema)
        media = round(sum(scores) / len(scores), 4) if scores else None
        out.append(TopicItem(tema=tema, menciones=n, sentimiento_medio=media))
    return out
