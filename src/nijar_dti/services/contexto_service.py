"""Lógica de negocio del contexto histórico (backfill de fuentes públicas).

Ingesta idempotente por clave natural (fuente, indicador, periodo, ámbito),
consulta de series y cálculo del factor de expansión calibrado contra las
pernoctaciones oficiales (INE EOH).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.connectors.contexto.expansion import (
    ESTANCIA_MEDIA_NOCHES,
    FactorExpansion,
    calcular_factor_expansion,
)
from nijar_dti.models.contexto import ContextoTuristico
from nijar_dti.schemas.contexto import (
    ContextoIngestResult,
    ContextoPunto,
    ContextoRecordIn,
    ContextoSerie,
)


async def ingerir_registros(
    db: AsyncSession, registros: list[ContextoRecordIn]
) -> ContextoIngestResult:
    """Ingesta idempotente: inserta nuevos y actualiza el valor de los existentes."""
    insertados = actualizados = 0
    ahora = datetime.now(UTC)

    for r in registros:
        existente = (
            await db.execute(
                select(ContextoTuristico).where(
                    ContextoTuristico.fuente == r.fuente,
                    ContextoTuristico.indicador == r.indicador,
                    ContextoTuristico.periodo == r.periodo,
                    ContextoTuristico.ambito == r.ambito,
                )
            )
        ).scalar_one_or_none()

        if existente is None:
            db.add(
                ContextoTuristico(
                    fuente=r.fuente,
                    indicador=r.indicador,
                    periodo=r.periodo,
                    valor=r.valor,
                    unidad=r.unidad,
                    ambito=r.ambito,
                    metadatos=r.metadatos,
                    capturado_en=ahora,
                )
            )
            insertados += 1
        else:
            existente.valor = r.valor
            existente.unidad = r.unidad
            existente.metadatos = r.metadatos
            existente.capturado_en = ahora
            actualizados += 1

    await db.flush()
    return ContextoIngestResult(
        recibidos=len(registros), insertados=insertados, actualizados=actualizados
    )


async def obtener_serie(
    db: AsyncSession, fuente: str, indicador: str, ambito: str | None = None
) -> ContextoSerie:
    q = select(ContextoTuristico).where(
        ContextoTuristico.fuente == fuente,
        ContextoTuristico.indicador == indicador,
    )
    if ambito:
        q = q.where(ContextoTuristico.ambito == ambito)
    q = q.order_by(ContextoTuristico.periodo)
    filas = (await db.execute(q)).scalars().all()
    return ContextoSerie(
        fuente=fuente,
        indicador=indicador,
        puntos=[
            ContextoPunto(
                periodo=f.periodo,
                valor=float(f.valor),
                unidad=f.unidad,
                ambito=f.ambito,
            )
            for f in filas
        ],
    )


async def factor_expansion(
    db: AsyncSession,
    periodo: str | None = None,
    muestra_periodo: int | None = None,
    estancia_media_noches: float = ESTANCIA_MEDIA_NOCHES,
) -> tuple[FactorExpansion, str | None]:
    """Calcula el factor de expansión usando las pernoctaciones EOH de ``periodo``.

    Si no se indica ``periodo``, usa el último disponible de la serie EOH.
    """
    q = select(ContextoTuristico).where(
        ContextoTuristico.fuente == "ine_eoh",
        ContextoTuristico.indicador == "pernoctaciones",
    )
    if periodo:
        q = q.where(ContextoTuristico.periodo == periodo)
    q = q.order_by(ContextoTuristico.periodo.desc())
    fila = (await db.execute(q)).scalars().first()

    pernoctaciones = float(fila.valor) if fila is not None else None
    periodo_ref = fila.periodo if fila is not None else periodo
    fe = calcular_factor_expansion(
        muestra_periodo=muestra_periodo,
        pernoctaciones_periodo=pernoctaciones,
        estancia_media_noches=estancia_media_noches,
    )
    return fe, periodo_ref
