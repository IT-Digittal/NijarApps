"""Métricas Prometheus para la API FastAPI.

Expone ``/metrics`` con métricas estándar (HTTP), KPIs específicos del
dominio (sensores, observaciones, chatbot, social) y métricas de salud.

Las métricas de dominio se exportan periódicamente mediante un job
asíncrono que consulta la BBDD cada ``METRICS_REFRESH_INTERVAL`` segundos.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import Response

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.models.faq import InteraccionChatbot
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.sensor import Sensor

log = logging.getLogger(__name__)

# Registro propio para no contaminar el global con métricas de tests.
REGISTRY = CollectorRegistry()

# ---- HTTP metrics ----
http_requests_total = Counter(
    "nijar_http_requests_total",
    "Número total de peticiones HTTP procesadas",
    ["method", "path", "status"],
    registry=REGISTRY,
)
http_request_duration_seconds = Histogram(
    "nijar_http_request_duration_seconds",
    "Latencia de las peticiones HTTP",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# ---- Domain gauges (refrescadas periódicamente) ----
sensores_total = Gauge(
    "nijar_sensores_total",
    "Número total de sensores registrados",
    ["estado"],
    registry=REGISTRY,
)
observaciones_ultima_hora = Gauge(
    "nijar_observaciones_ultima_hora_total",
    "Observaciones IoT recibidas en la última hora",
    registry=REGISTRY,
)
observaciones_invalidas_ultima_hora = Gauge(
    "nijar_observaciones_invalidas_ultima_hora_total",
    "Observaciones inválidas (fuera de rango) en la última hora",
    registry=REGISTRY,
)
chatbot_interacciones_ultimas_24h = Gauge(
    "nijar_chatbot_interacciones_ultimas_24h_total",
    "Interacciones del chatbot en las últimas 24 horas",
    ["nivel_confianza"],
    registry=REGISTRY,
)
opiniones_ultimas_24h = Gauge(
    "nijar_opiniones_ultimas_24h_total",
    "Menciones capturadas por Social Listening en las últimas 24 horas",
    ["fuente", "sentimiento"],
    registry=REGISTRY,
)

# ---- Health metrics ----
db_up = Gauge("nijar_db_up", "1 si la BBDD responde, 0 si no", registry=REGISTRY)
last_metrics_refresh = Gauge(
    "nijar_metrics_last_refresh_timestamp",
    "Timestamp del último refresco de métricas de dominio",
    registry=REGISTRY,
)


async def metrics_endpoint(request: Request) -> Response:
    """Endpoint /metrics para Prometheus."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


async def refresh_domain_metrics() -> None:
    """Calcula las métricas de dominio leyendo de la BBDD."""
    try:
        async with AsyncSessionLocal() as db:
            ahora = datetime.now(UTC)
            hace_1h = ahora - timedelta(hours=1)
            hace_24h = ahora - timedelta(hours=24)

            # Sensores por estado
            for estado in (
                "operativo",
                "offline",
                "mantenimiento",
                "averia",
                "bateria_baja",
                "desconocido",
            ):
                n = int(
                    (
                        await db.execute(
                            select(func.count()).select_from(Sensor).where(Sensor.estado == estado)
                        )
                    ).scalar_one()
                    or 0
                )
                sensores_total.labels(estado=estado).set(n)

            # Observaciones última hora
            obs_total = int(
                (
                    await db.execute(
                        select(func.count())
                        .select_from(Observacion)
                        .where(Observacion.observado_en >= hace_1h)
                    )
                ).scalar_one()
                or 0
            )
            obs_invalid = int(
                (
                    await db.execute(
                        select(func.count())
                        .select_from(Observacion)
                        .where(Observacion.observado_en >= hace_1h)
                        .where(Observacion.valido.is_(False))
                    )
                ).scalar_one()
                or 0
            )
            observaciones_ultima_hora.set(obs_total)
            observaciones_invalidas_ultima_hora.set(obs_invalid)

            # Chatbot últimas 24h por nivel de confianza
            for nivel in ("alta", "media", "fuera_de_dominio"):
                n = int(
                    (
                        await db.execute(
                            select(func.count())
                            .select_from(InteraccionChatbot)
                            .where(InteraccionChatbot.created_at >= hace_24h)
                            .where(InteraccionChatbot.nivel_confianza == nivel)
                        )
                    ).scalar_one()
                    or 0
                )
                chatbot_interacciones_ultimas_24h.labels(nivel_confianza=nivel).set(n)

            # Opiniones últimas 24h por fuente y sentimiento
            res = await db.execute(
                select(Opinion.fuente, Opinion.sentimiento, func.count(Opinion.id))
                .where(Opinion.publicado_en >= hace_24h)
                .group_by(Opinion.fuente, Opinion.sentimiento)
            )
            for fuente, sentimiento, count in res.all():
                opiniones_ultimas_24h.labels(
                    fuente=str(fuente),
                    sentimiento=str(sentimiento),
                ).set(int(count or 0))

            db_up.set(1)
            last_metrics_refresh.set(ahora.timestamp())
    except Exception as exc:  # noqa: BLE001
        log.warning("No se pudo refrescar métricas de dominio: %s", exc)
        db_up.set(0)


async def metrics_loop(interval_seconds: int = 60) -> None:
    """Loop que refresca métricas cada N segundos."""
    while True:
        await refresh_domain_metrics()
        await asyncio.sleep(interval_seconds)
