"""Lógica de negocio del contexto histórico (backfill de fuentes públicas).

Ingesta idempotente por clave natural (fuente, indicador, periodo, ámbito),
consulta de series y cálculo del factor de expansión calibrado contra las
pernoctaciones oficiales (INE EOH).
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.connectors.contexto.base import FuentePublicaConnector
from nijar_dti.connectors.contexto.expansion import (
    ESTANCIA_MEDIA_NOCHES,
    FactorExpansion,
    calcular_factor_expansion,
)
from nijar_dti.connectors.contexto.fuentes import todos_los_conectores
from nijar_dti.core.logging import get_logger
from nijar_dti.models.contexto import ContextoTuristico
from nijar_dti.schemas.contexto import (
    ContextoIngestResult,
    ContextoPunto,
    ContextoRecordIn,
    ContextoSerie,
)

logger = get_logger(__name__)
MADRID = ZoneInfo("Europe/Madrid")
_CERROJO_CONTEXTO = (
    17_010_945  # pg_advisory_xact_lock: una sola descarga aunque haya varios workers
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
                    fuente=r.fuente,  # type: ignore[arg-type]
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


# ------------------------------------------------- actualización desde fuentes --
def _es_sintetico():
    return func.coalesce(ContextoTuristico.metadatos["sintetico"].as_string(), "false") == "true"


async def actualizar_desde_fuentes(
    db: AsyncSession,
    anios: int | None = None,
    conectores: list[FuentePublicaConnector] | None = None,
) -> dict[str, str]:
    """Descarga las series reales de INE, Junta y AENA y las guarda.

    Cada fuente es independiente: si una falla se conserva lo que ya hubiera
    (real o de demostración) y se sigue con las demás. Cuando una fuente
    devuelve datos reales se borran sus series sintéticas, para que el panel
    no mezcle meses inventados con datos oficiales.
    """
    anios = anios or get_settings().contexto_backfill_anios
    resultado: dict[str, str] = {}
    for conector in conectores or todos_los_conectores(dry_run=False):
        try:
            registros = await asyncio.to_thread(conector.fetch_series, anios)
        except Exception as exc:  # noqa: BLE001 — una fuente caída no frena las demás
            logger.warning(
                "Fuente de contexto no disponible", fuente=conector.fuente, error=str(exc)
            )
            resultado[conector.fuente] = f"error: {exc}"
            continue
        if not registros:
            resultado[conector.fuente] = "sin datos"
            continue
        await db.execute(
            delete(ContextoTuristico).where(
                ContextoTuristico.fuente == conector.fuente, _es_sintetico()
            )
        )
        r = await ingerir_registros(db, [ContextoRecordIn(**asdict(x)) for x in registros])
        resultado[conector.fuente] = (
            f"{r.recibidos} registros ({registros[0].periodo} a {registros[-1].periodo})"
        )
    return resultado


def _segundos_hasta(hora: int, ahora: datetime | None = None) -> float:
    ahora = ahora or datetime.now(MADRID)
    objetivo = ahora.replace(hour=hora, minute=45, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    return (objetivo - ahora).total_seconds()


async def _hay_series_sinteticas(db: AsyncSession) -> bool:
    n = (await db.execute(select(func.count()).where(_es_sintetico()))).scalar_one()
    return bool(n)


async def actualizacion_diaria_loop(hora: int) -> None:
    """Refresca cada día las series oficiales (el INE y AENA publican a mitad de mes).

    Si al arrancar aún quedan series de demostración, la primera descarga se
    hace a los pocos minutos en lugar de esperar al día siguiente.
    """
    from nijar_dti.core.database import AsyncSessionLocal

    primera = True
    while True:
        espera = _segundos_hasta(hora)
        if primera:
            primera = False
            try:
                async with AsyncSessionLocal() as db:
                    if await _hay_series_sinteticas(db):
                        espera = 120
            except Exception as exc:  # noqa: BLE001
                logger.warning("No se pudo revisar el contexto al arrancar", error=str(exc))
        await asyncio.sleep(espera)
        try:
            async with AsyncSessionLocal() as db:
                libre = (
                    await db.execute(
                        text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": _CERROJO_CONTEXTO}
                    )
                ).scalar()
                if not libre:
                    # otro worker de uvicorn ya está descargando las series
                    await asyncio.sleep(60)
                    continue
                resultado = await actualizar_desde_fuentes(db)
                await db.commit()
            logger.info("Contexto oficial actualizado", resultado=resultado)
        except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
            logger.error("Error al actualizar el contexto oficial", error=str(exc))
        await asyncio.sleep(60)
