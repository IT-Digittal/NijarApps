"""Pipeline de Social Listening.

Orquesta:

1. Llamada a los conectores configurados (Twitter, Facebook, Instagram).
2. Análisis NLP de cada mención (idioma, sentimiento, temas, entidades).
3. Persistencia idempotente en BBDD (deduplicación por
   ``fuente`` + ``fuente_id_externo``).
4. Métricas operativas para reporting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.social.base import MentionRaw, SocialListeningConnector
from nijar_dti.connectors.social.nlp import (
    analizar_sentimiento,
    detectar_entidades,
    detectar_idioma,
    extraer_temas,
)
from nijar_dti.models.opinion import FuenteOpinion, Opinion, Sentimiento

log = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    capturadas: int = 0
    nuevas: int = 0
    duplicadas: int = 0
    errores: int = 0
    por_fuente: dict[str, int] = field(default_factory=dict)


def _to_sentimiento(etiqueta: str) -> Sentimiento:
    try:
        return Sentimiento(etiqueta)
    except ValueError:
        return Sentimiento.DESCONOCIDO


def _to_fuente(value: str) -> FuenteOpinion:
    try:
        return FuenteOpinion(value)
    except ValueError:
        return FuenteOpinion.OTRO


async def _ya_existe(db: AsyncSession, fuente: str, externo_id: str) -> bool:
    res = await db.execute(
        select(Opinion.id)
        .where(Opinion.fuente == fuente)
        .where(Opinion.fuente_id_externo == externo_id)
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


async def procesar_mencion(db: AsyncSession, mention: MentionRaw, stats: PipelineStats) -> None:
    if await _ya_existe(db, mention.fuente, mention.fuente_id_externo):
        stats.duplicadas += 1
        return

    idioma = mention.idioma or detectar_idioma(mention.texto_original)
    analisis = analizar_sentimiento(mention.texto_original, idioma=idioma)
    temas = extraer_temas(mention.texto_original)
    entidades = detectar_entidades(mention.texto_original)

    metricas = {
        k: v
        for k, v in {
            "likes": mention.likes,
            "compartidos": mention.compartidos,
            "comentarios": mention.comentarios,
            "alcance": mention.alcance,
        }.items()
        if v is not None
    }

    opinion = Opinion(
        fuente=_to_fuente(mention.fuente),
        texto_original=mention.texto_original,
        publicado_en=mention.publicado_en,
        fuente_id_externo=mention.fuente_id_externo,
        autor_handle=mention.autor_handle,
        idioma=idioma,
        sentimiento=_to_sentimiento(analisis.etiqueta),
        score_sentimiento=analisis.score,
        temas=temas or None,
        entidades_mencionadas=entidades or None,
        metricas=metricas or None,
        latitud=mention.latitud,
        longitud=mention.longitud,
        capturado_en=datetime.now(UTC),
        payload_original=mention.payload_original or None,
    )
    db.add(opinion)
    stats.nuevas += 1


async def ejecutar_poll(
    db: AsyncSession,
    conectores: list[SocialListeningConnector],
    desde: datetime | None,
    settings: Settings | None = None,
) -> PipelineStats:
    """Ejecuta un ciclo completo de captura sobre todos los conectores."""
    settings = settings or get_settings()
    stats = PipelineStats()

    for conector in conectores:
        if not settings.social_dry_run and not conector.is_configured:
            log.info("Conector %s sin credenciales, saltando", conector.fuente)
            continue
        try:
            menciones = await conector.fetch_mentions(since=desde)
        except Exception as exc:  # noqa: BLE001
            log.exception("Error en conector %s: %s", conector.fuente, exc)
            stats.errores += 1
            continue

        stats.por_fuente[conector.fuente] = len(menciones)
        stats.capturadas += len(menciones)

        for mention in menciones:
            try:
                await procesar_mencion(db, mention, stats)
            except Exception as exc:  # noqa: BLE001
                log.exception("Error procesando mención: %s", exc)
                stats.errores += 1

    await db.commit()
    log.info(
        "Poll Social Listening completado — capturadas=%d nuevas=%d duplicadas=%d errores=%d",
        stats.capturadas,
        stats.nuevas,
        stats.duplicadas,
        stats.errores,
    )
    return stats
