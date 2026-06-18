"""Lógica de negocio de los modelos predictivos de afluencia (A.2 / A.3).

Construye la serie diaria de afluencia desde la BBDD (visitas a tótem/web/app
o consultas al chatbot), ajusta el modelo estacional y expone predicción,
validación MAPE y detección de anomalías. La lógica matemática vive en
``connectors/analytics/forecasting.py`` (pura y testeable).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.connectors.analytics.forecasting import (
    ajustar_modelo_estacional,
    detectar_anomalias,
    prever_serie,
    rellenar_dias,
    validar_holdout,
)
from nijar_dti.models.faq import InteraccionChatbot
from nijar_dti.models.visita import TipoVisita, Visita
from nijar_dti.schemas.prediccion import (
    AnomaliaPunto,
    DeteccionAnomalias,
    PrediccionAfluencia,
    PrediccionPunto,
    ValidacionModelo,
)

# Métricas soportadas -> cómo se obtiene su serie diaria
_METRICAS_VISITA = {
    "totem": TipoVisita.INTERACCION_TOTEM,
    "web": TipoVisita.WEB_VISTA,
    "app": TipoVisita.APP_VISTA,
}
METRICAS_VALIDAS = (*_METRICAS_VISITA.keys(), "chatbot")

_Z_BANDA = 1.96  # banda de confianza al 95 %


async def _serie_diaria(
    db: AsyncSession, metrica: str, desde: datetime, hasta: datetime
) -> list:
    """Serie diaria continua (rellena con 0) de la métrica indicada."""
    if metrica in _METRICAS_VISITA:
        bucket = func.date_trunc("day", Visita.ocurrido_en).label("dia")
        q = (
            select(bucket, func.count().label("n"))
            .where(
                Visita.tipo == _METRICAS_VISITA[metrica],
                Visita.ocurrido_en >= desde,
                Visita.ocurrido_en <= hasta,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
    elif metrica == "chatbot":
        bucket = func.date_trunc("day", InteraccionChatbot.created_at).label("dia")
        q = (
            select(bucket, func.count().label("n"))
            .where(
                InteraccionChatbot.created_at >= desde,
                InteraccionChatbot.created_at <= hasta,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
    else:
        raise ValueError(f"Métrica no soportada: {metrica}")

    filas = (await db.execute(q)).all()
    conteos: dict[date, float] = {}
    for dia, n in filas:
        d = dia.date() if isinstance(dia, datetime) else dia
        conteos[d] = float(n)
    return rellenar_dias(conteos, desde.date(), hasta.date())


async def prediccion_afluencia(
    db: AsyncSession,
    metrica: str,
    horizonte_dias: int = 14,
    dias_historico: int = 365,
) -> PrediccionAfluencia:
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=dias_historico)
    serie = await _serie_diaria(db, metrica, desde, hasta)

    modelo = ajustar_modelo_estacional(serie)
    validacion = validar_holdout(serie)
    inicio = hasta.date() + timedelta(days=1)
    previsiones = prever_serie(modelo, inicio, horizonte_dias)

    margen = _Z_BANDA * modelo.sigma_residuo
    puntos = [
        PrediccionPunto(
            fecha=p.fecha,
            valor_estimado=p.valor,
            banda_inferior=round(max(p.valor - margen, 0.0), 2),
            banda_superior=round(p.valor + margen, 2),
        )
        for p in previsiones
    ]

    return PrediccionAfluencia(
        metrica=metrica,
        horizonte_dias=horizonte_dias,
        dias_historico=len(serie),
        generado_en=hasta,
        mape_validacion=validacion.mape,
        cumple_umbral_mape=validacion.cumple_umbral,
        puntos=puntos,
    )


async def validacion_modelo(
    db: AsyncSession,
    metrica: str,
    dias_historico: int = 365,
    dias_test: int = 14,
) -> ValidacionModelo:
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=dias_historico)
    serie = await _serie_diaria(db, metrica, desde, hasta)
    r = validar_holdout(serie, dias_test=dias_test)
    return ValidacionModelo(
        metrica=metrica,
        mape=r.mape,
        umbral=r.umbral,
        cumple_umbral=r.cumple_umbral,
        n_test=r.n_test,
        n_evaluable=r.n_evaluable,
        dias_holdout=r.dias_holdout,
    )


async def anomalias_afluencia(
    db: AsyncSession,
    metrica: str,
    dias_historico: int = 180,
    z: float = 3.0,
) -> DeteccionAnomalias:
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=dias_historico)
    serie = await _serie_diaria(db, metrica, desde, hasta)
    anomalias = detectar_anomalias(serie, z=z)
    return DeteccionAnomalias(
        metrica=metrica,
        desde=desde.date(),
        hasta=hasta.date(),
        umbral_sigmas=z,
        total_evaluado=len(serie),
        anomalias=[
            AnomaliaPunto(
                fecha=a.fecha,
                valor=a.valor,
                valor_esperado=a.valor_esperado,
                desviacion_sigmas=a.desviacion_sigmas,
            )
            for a in anomalias
        ],
    )
