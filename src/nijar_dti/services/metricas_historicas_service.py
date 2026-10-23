"""Captura mensual del histórico de métricas por vertical.

La tabla ``metricas_historicas`` arranca con 2 años de histórico de EJEMPLO
(seed de instalación, ``origen="ejemplo"``). Este servicio guarda cada mes el
valor REAL de las fuentes ya integradas, sustituyendo el punto de ejemplo del
mismo periodo (o añadiendo los meses nuevos):

==========  ==============  =============================================  =========
vertical    indicador       fuente                                         origen
==========  ==============  =============================================  =========
energia     consumo_kwh     Datadis: CUPS municipales salvo alumbrado       datadis
energia     coste_eur       consumo real × €/kWh medio de los suministros   estimado
alumbrado   consumo_kwh     Datadis: curva horaria de los CUPS de alumbrado datadis
==========  ==============  =============================================  =========

Los CUPS de alumbrado se cuentan solo en ``alumbrado`` (la portada suma ambos
para el gasto eléctrico total, sin duplicar).

Agua (concesionaria), residuos (siGEUS), accesos (aforos) e incidencias de
seguridad (112 / Policía Local) se añadirán al registro ``CAPTURADORES`` en
cuanto esas fuentes estén integradas; hasta entonces su histórico sigue siendo
el de ejemplo y el panel lo indica.

Solo se guarda un mes cuando está **cerrado y completo** (la curva cubre todos
sus días, salvo un margen de 2 por el retraso de Datadis): nunca se registra un
mes a medias como si fuera el total.
"""

from __future__ import annotations

import asyncio
import calendar
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.core.logging import get_logger
from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia
from nijar_dti.models.metrica_historica import MetricaHistorica
from nijar_dti.models.verticales import SuministroEnergia

logger = get_logger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
FUENTE_DATADIS = "datadis"
ORIGENES_REALES = frozenset({"datadis"})
MARGEN_DIAS = 2  # días sin lectura tolerados al final de un mes (retraso de Datadis)
_CERROJO_CAPTURA = 18_002_026  # clave del pg_advisory_xact_lock (una captura a la vez)


@dataclass(frozen=True)
class ValorCapturado:
    vertical: str
    indicador: str
    periodo: str
    valor: float
    unidad: str
    origen: str


# ------------------------------------------------------------ utilidades -----
def periodo_de(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def periodo_anterior(hoy: date) -> str:
    """Último mes cerrado respecto a ``hoy``."""
    primero = hoy.replace(day=1)
    return periodo_de(primero - timedelta(days=1))


def periodos_entre(desde: str, hasta: str) -> list[str]:
    """Periodos mensuales de ``desde`` a ``hasta`` (ambos incluidos)."""
    y, m = int(desde[:4]), int(desde[5:7])
    yh, mh = int(hasta[:4]), int(hasta[5:7])
    salida: list[str] = []
    while (y, m) <= (yh, mh):
        salida.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return salida


def rango_mes(periodo: str) -> tuple[datetime, datetime, int]:
    """Inicio y fin (UTC, fin exclusivo) del mes en hora de Madrid, y nº de días."""
    y, m = int(periodo[:4]), int(periodo[5:7])
    dias = calendar.monthrange(y, m)[1]
    inicio = datetime.combine(date(y, m, 1), time(0), tzinfo=MADRID)
    siguiente = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    fin = datetime.combine(siguiente, time(0), tzinfo=MADRID)
    return inicio, fin, dias


def mes_completo(dias_con_dato: int, dias_mes: int) -> bool:
    return dias_con_dato >= dias_mes - MARGEN_DIAS


def es_real(origen: str | None) -> bool:
    return (origen or "ejemplo") in ORIGENES_REALES


# ------------------------------------------------------------ capturadores ---
async def _cups_reales(db: AsyncSession, *, alumbrado: bool) -> list[SuministroEnergia]:
    """Suministros reales de Datadis: los de alumbrado público o el resto (edificios)."""
    q = select(SuministroEnergia).where(
        SuministroEnergia.metadatos["fuente"].as_string() == FUENTE_DATADIS
    )
    filas = list((await db.execute(q)).scalars().all())
    return [s for s in filas if ((s.tipo or "").lower() == "alumbrado") == alumbrado]


async def _consumo_curva(db: AsyncSession, cups: list[str], periodo: str) -> float | None:
    """kWh del mes desde la curva horaria; None si el mes no está completo."""
    if not cups:
        return None
    inicio, fin, dias = rango_mes(periodo)
    dia_local = func.date(func.timezone("Europe/Madrid", ConsumoHorarioEnergia.momento))
    total, dias_con_dato = (
        await db.execute(
            select(
                func.coalesce(func.sum(ConsumoHorarioEnergia.consumo_kwh), 0),
                func.count(func.distinct(dia_local)),
            ).where(
                ConsumoHorarioEnergia.cups.in_(cups),
                ConsumoHorarioEnergia.momento >= inicio,
                ConsumoHorarioEnergia.momento < fin,
            )
        )
    ).one()
    if not mes_completo(int(dias_con_dato or 0), dias):
        return None
    return round(float(total or 0), 2)


async def _capturar_energia(db: AsyncSession, periodo: str) -> list[ValorCapturado]:
    sums = await _cups_reales(db, alumbrado=False)
    consumo = await _consumo_curva(db, [s.cups for s in sums], periodo)
    if consumo is None:
        return []
    # €/kWh medio de los suministros reales (si no hay coste, el precio de config)
    kwh = sum(float(s.consumo_mes_kwh or 0) for s in sums)
    eur = sum(float(s.coste_mes_eur or 0) for s in sums)
    precio = eur / kwh if kwh and eur else get_settings().precio_kwh_eur
    return [
        ValorCapturado("energia", "consumo_kwh", periodo, consumo, "kWh", "datadis"),
        ValorCapturado(
            "energia", "coste_eur", periodo, round(consumo * precio, 2), "€", "estimado"
        ),
    ]


async def _capturar_alumbrado(db: AsyncSession, periodo: str) -> list[ValorCapturado]:
    sums = await _cups_reales(db, alumbrado=True)
    consumo = await _consumo_curva(db, [s.cups for s in sums], periodo)
    if consumo is None:
        return []
    return [ValorCapturado("alumbrado", "consumo_kwh", periodo, consumo, "kWh", "datadis")]


Capturador = Callable[[AsyncSession, str], Awaitable[list[ValorCapturado]]]

# Registro de fuentes reales. Para integrar una nueva (siGEUS, concesionaria del
# agua, aforos…) basta con añadir aquí su capturador.
CAPTURADORES: dict[str, Capturador] = {
    "energia": _capturar_energia,
    "alumbrado": _capturar_alumbrado,
}


# ------------------------------------------------------------ escritura ------
async def guardar(db: AsyncSession, valores: list[ValorCapturado]) -> None:
    """Inserta o sustituye (mismo vertical + indicador + periodo) cada valor."""
    for v in valores:
        stmt = insert(MetricaHistorica).values(
            id=uuid4(),
            vertical=v.vertical,
            indicador=v.indicador,
            periodo=v.periodo,
            valor=v.valor,
            unidad=v.unidad,
            origen=v.origen,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["vertical", "indicador", "periodo"],
            set_={
                "valor": stmt.excluded.valor,
                "unidad": stmt.excluded.unidad,
                "origen": stmt.excluded.origen,
                "updated_at": func.now(),
            },
        )
        await db.execute(stmt)


async def capturar_mes(
    db: AsyncSession, periodo: str, *, guardar_cambios: bool = True
) -> list[ValorCapturado]:
    """Calcula (y guarda) los valores reales disponibles para ``periodo``."""
    valores: list[ValorCapturado] = []
    for nombre, capturador in CAPTURADORES.items():
        try:
            valores.extend(await capturador(db, periodo))
        except Exception as exc:  # noqa: BLE001 — una fuente caída no frena las demás
            logger.error(
                "Fallo al capturar métricas", fuente=nombre, periodo=periodo, error=str(exc)
            )
    if guardar_cambios and valores:
        await guardar(db, valores)
    return valores


async def estado(db: AsyncSession) -> dict[str, Any]:
    """Resumen por indicador: meses de ejemplo, meses reales y último periodo."""
    filas = (
        await db.execute(
            select(
                MetricaHistorica.vertical,
                MetricaHistorica.indicador,
                MetricaHistorica.origen,
                func.count(),
                func.max(MetricaHistorica.periodo),
            ).group_by(
                MetricaHistorica.vertical, MetricaHistorica.indicador, MetricaHistorica.origen
            )
        )
    ).all()
    salida: dict[str, Any] = {}
    for vertical, indicador, origen, n, ultimo in filas:
        d = salida.setdefault(f"{vertical}.{indicador}", {})
        d[str(origen)] = {"meses": int(n), "ultimo": str(ultimo)}
    return salida


# ------------------------------------------------------------ tarea diaria ---
def _segundos_hasta(hora: int, ahora: datetime | None = None) -> float:
    ahora = ahora or datetime.now(MADRID)
    objetivo = ahora.replace(hour=hora, minute=30, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    return (objetivo - ahora).total_seconds()


async def captura_mensual_loop(hora: int) -> None:
    """Cada día (hora de Madrid) intenta guardar el último mes cerrado.

    Se repite a diario porque Datadis publica con unos días de retraso: el mes
    se registra en cuanto su curva está completa y se refresca si llegan
    lecturas corregidas. Un cerrojo de PostgreSQL evita capturas simultáneas.
    """
    from nijar_dti.core.database import AsyncSessionLocal

    while True:
        await asyncio.sleep(_segundos_hasta(hora))
        try:
            async with AsyncSessionLocal() as db:
                libre = (
                    await db.execute(
                        text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": _CERROJO_CAPTURA}
                    )
                ).scalar()
                if not libre:
                    continue
                periodo = periodo_anterior(datetime.now(MADRID).date())
                valores = await capturar_mes(db, periodo)
                await db.commit()
            logger.info(
                "Captura mensual de métricas",
                periodo=periodo,
                indicadores=[f"{v.vertical}.{v.indicador}" for v in valores],
            )
        except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
            logger.error("Error en la captura mensual de métricas", error=str(exc))
        await asyncio.sleep(60)
