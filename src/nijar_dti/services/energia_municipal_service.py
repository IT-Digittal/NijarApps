"""Análisis real de los suministros eléctricos municipales (Datadis privado).

Alimenta las pantallas del vertical «Energía municipal» con los CUPS que el
Ayuntamiento ha autorizado en Datadis y su curva horaria:

- **Resumen**: consumo y coste del último mes cerrado, reparto alumbrado /
  edificios, evolución mensual, CO₂, interanual y recomendaciones.
- **Suministros**: los CUPS uno a uno, con consumo, variación, pico horario,
  potencia contratada y estado de las lecturas.
- **Costes y contratos**: potencia contratada frente al pico real. Si el mayor
  consumo horario de los últimos 12 meses no llega a la mitad de la potencia
  contratada, se propone una potencia con margen y se estima el ahorro anual
  del término de potencia.
- **Autoconsumo**: energía autoconsumida y excedentes que publica Datadis.

Todo sale de ``energia_suministros`` (``metadatos.fuente = "datadis"``) y
``energia_consumos_horarios``; los costes son estimados (consumo × precio medio
del kWh de la configuración), porque Datadis no da facturas.

El cálculo agrega millones de lecturas, así que se guarda en memoria unos
minutos (``CACHE_SEGUNDOS``) y se invalida cuando entra una lectura nueva.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia
from nijar_dti.models.verticales import SuministroEnergia
from nijar_dti.schemas.direccion import RecomendacionIA
from nijar_dti.schemas.verticales import (
    DetalleSuministroEnergia,
    MesConsumoEnergia,
    RecomendacionEnergia,
    ResumenEnergiaMunicipal,
    SuministroAnalisis,
)
from nijar_dti.services.energia_anexos_service import es_dia_valle

MADRID = ZoneInfo("Europe/Madrid")
FUENTE = "datadis"
CACHE_SEGUNDOS = 600
MESES_HISTORICO = 24
UTILIZACION_REVISAR = 0.5  # pico horario < 50 % de la potencia contratada → revisar
MARGEN_POTENCIA = 1.3  # el pico de 15 min supera al horario: margen del 30 %
MESES_MINIMOS_POTENCIA = 6  # no se recomienda nada con menos historia
DIAS_SIN_LECTURA = 10  # Datadis publica con 1-3 días de retraso
SUBIDA_ALERTA_PCT = 25.0
SUBIDA_ALERTA_KWH = 500.0


# ------------------------------------------------------------ utilidades -----
def periodo_de(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def mes_anterior(periodo: str, n: int = 1) -> str:
    y, m = int(periodo[:4]), int(periodo[5:7])
    total = y * 12 + (m - 1) - n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def ultimo_mes_cerrado(hoy: date) -> str:
    return periodo_de(hoy.replace(day=1) - timedelta(days=1))


def dias_del_mes(periodo: str) -> int:
    y, m = int(periodo[:4]), int(periodo[5:7])
    sig = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return (sig - date(y, m, 1)).days


def miles(n: float) -> str:
    """1234567 → «1.234.567» (formato español, sin decimales)."""
    return f"{n:,.0f}".replace(",", ".")


def suministros(n: int) -> str:
    return f"{n} suministro" if n == 1 else f"{n} suministros"


def variacion(actual: float | None, previo: float | None) -> float | None:
    if actual is None or not previo:
        return None
    return round((actual - previo) / previo * 100, 1)


def _contrato(meta: dict[str, Any]) -> dict[str, Any]:
    c = meta.get("contrato")
    return c if isinstance(c, dict) else {}


def tipo_de(s: SuministroEnergia) -> str:
    return "alumbrado" if (s.tipo or "").lower() == "alumbrado" else "edificio"


def potencia_de(s: SuministroEnergia) -> float | None:
    """Mayor potencia contratada (P1…P6 del contrato, o la guardada en la fila)."""
    meta = s.metadatos if isinstance(s.metadatos, dict) else {}
    pots = [p for p in _contrato(meta).get("potencias_kw") or [] if isinstance(p, int | float)]
    if pots:
        return float(max(pots))
    valor = float(s.potencia_contratada_kw or 0)
    return valor or None


def potencia_recomendada(pico_kw: float) -> float:
    """Pico horario × margen, redondeado hacia arriba a 0,5 kW (mínimo 1 kW)."""
    return max(1.0, math.ceil(pico_kw * MARGEN_POTENCIA * 2) / 2)


def analisis_potencia(
    potencia_kw: float | None, pico_kw: float | None, meses_con_datos: int, precio_kw_anio: float
) -> tuple[float | None, float | None, float | None]:
    """(utilización %, potencia recomendada, ahorro €/año) de un suministro."""
    if not potencia_kw or pico_kw is None:
        return None, None, None
    utilizacion = round(pico_kw / potencia_kw * 100, 1)
    if meses_con_datos < MESES_MINIMOS_POTENCIA or pico_kw / potencia_kw >= UTILIZACION_REVISAR:
        return utilizacion, None, None
    recomendada = potencia_recomendada(pico_kw)
    if recomendada >= potencia_kw:
        return utilizacion, None, None
    return utilizacion, recomendada, round((potencia_kw - recomendada) * precio_kw_anio, 0)


# ------------------------------------------------------------ consultas ------
def _hora_local() -> Any:
    return func.timezone(literal_column("'Europe/Madrid'"), ConsumoHorarioEnergia.momento)


def _mes_local() -> Any:
    return func.to_char(_hora_local(), literal_column("'YYYY-MM'"))


@dataclass
class DatosCups:
    meses: dict[str, float] = field(default_factory=dict)  # AAAA-MM → kWh
    dias_mes: dict[str, int] = field(default_factory=dict)  # AAAA-MM → días con lectura
    autoconsumo: dict[str, float] = field(default_factory=dict)
    excedente: dict[str, float] = field(default_factory=dict)
    pico_kw: float | None = None
    pico_momento: datetime | None = None
    ultima: datetime | None = None


@dataclass
class Analisis:
    hoy: date
    periodo: str
    sums: list[SuministroEnergia]
    datos: dict[str, DatosCups]
    filas: list[SuministroAnalisis]
    creado: float


_cache: dict[str, Analisis] = {}


async def _ultima_lectura(db: AsyncSession) -> datetime | None:
    return (await db.execute(select(func.max(ConsumoHorarioEnergia.momento)))).scalar_one_or_none()


async def suministros_reales(db: AsyncSession) -> list[SuministroEnergia]:
    q = select(SuministroEnergia).where(SuministroEnergia.metadatos["fuente"].as_string() == FUENTE)
    return list((await db.execute(q)).scalars().all())


async def _datos_por_cups(db: AsyncSession, cups: list[str], desde: date) -> dict[str, DatosCups]:
    """Consumo mensual, días con lectura, autoconsumo/excedentes, pico y última lectura."""
    datos: dict[str, DatosCups] = defaultdict(DatosCups)
    if not cups:
        return {}
    inicio = datetime.combine(desde, datetime.min.time(), tzinfo=MADRID)
    filtro = (ConsumoHorarioEnergia.cups.in_(cups), ConsumoHorarioEnergia.momento >= inicio)
    mes = _mes_local()
    dia = func.date(_hora_local())
    for c, periodo, kwh, auto, exc, dias in (
        await db.execute(
            select(
                ConsumoHorarioEnergia.cups,
                mes,
                func.sum(ConsumoHorarioEnergia.consumo_kwh),
                func.sum(func.coalesce(ConsumoHorarioEnergia.autoconsumo_kwh, 0)),
                func.sum(func.coalesce(ConsumoHorarioEnergia.excedente_kwh, 0)),
                func.count(func.distinct(dia)),
            )
            .where(*filtro)
            .group_by(ConsumoHorarioEnergia.cups, mes)
        )
    ).all():
        d = datos[c]
        d.meses[periodo] = float(kwh or 0)
        d.autoconsumo[periodo] = float(auto or 0)
        d.excedente[periodo] = float(exc or 0)
        d.dias_mes[periodo] = int(dias or 0)

    # Pico horario de los últimos 12 meses (DISTINCT ON: la hora de mayor consumo por CUPS)
    hace_un_anio = datetime.now(UTC) - timedelta(days=365)
    picos = (
        await db.execute(
            select(
                ConsumoHorarioEnergia.cups,
                ConsumoHorarioEnergia.consumo_kwh,
                ConsumoHorarioEnergia.momento,
            )
            .where(
                ConsumoHorarioEnergia.cups.in_(cups), ConsumoHorarioEnergia.momento >= hace_un_anio
            )
            .distinct(ConsumoHorarioEnergia.cups)
            .order_by(ConsumoHorarioEnergia.cups, ConsumoHorarioEnergia.consumo_kwh.desc())
        )
    ).all()
    for c, kwh, momento in picos:
        datos[c].pico_kw = float(kwh or 0)
        datos[c].pico_momento = momento
    for c, ultima in (
        await db.execute(
            select(ConsumoHorarioEnergia.cups, func.max(ConsumoHorarioEnergia.momento))
            .where(ConsumoHorarioEnergia.cups.in_(cups))
            .group_by(ConsumoHorarioEnergia.cups)
        )
    ).all():
        datos[c].ultima = ultima
    return dict(datos)


def _ultimos_12(periodo: str) -> list[str]:
    return [mes_anterior(periodo, i) for i in range(11, -1, -1)]


def fila_suministro(
    s: SuministroEnergia, d: DatosCups | None, periodo: str, ahora: datetime
) -> SuministroAnalisis:
    cfg = get_settings()
    d = d or DatosCups()
    meta = s.metadatos if isinstance(s.metadatos, dict) else {}
    contrato = _contrato(meta)
    potencia = potencia_de(s)
    mes = d.meses.get(periodo)
    previo = d.meses.get(mes_anterior(periodo))
    anio_antes = d.meses.get(mes_anterior(periodo, 12))
    meses_validos = [p for p, n in d.dias_mes.items() if n >= dias_del_mes(p) - 2]
    utilizacion, recomendada, ahorro = analisis_potencia(
        potencia, d.pico_kw, len(meses_validos), cfg.precio_potencia_kw_anio_eur
    )
    dias_sin = (ahora - d.ultima).days if d.ultima else None
    if d.ultima is None:
        estado = "sin_datos"
    elif dias_sin is not None and dias_sin > DIAS_SIN_LECTURA:
        estado = "sin_datos_recientes"
    else:
        estado = "ok"
    ultimos = _ultimos_12(periodo)
    return SuministroAnalisis(
        cups=s.cups,
        direccion=str(meta.get("direccion") or s.edificio or s.cups),
        tipo=tipo_de(s),
        tarifa=contrato.get("tarifa_acceso"),
        potencia_contratada_kw=potencia,
        consumo_mes_kwh=round(mes or 0.0, 1),
        consumo_mes_anterior_kwh=round(previo or 0.0, 1),
        variacion_mes_pct=variacion(mes, previo),
        consumo_mismo_mes_anio_anterior_kwh=round(anio_antes, 1) if anio_antes else None,
        variacion_interanual_pct=variacion(mes, anio_antes),
        consumo_12m_kwh=round(sum(d.meses.get(p, 0.0) for p in ultimos), 1),
        coste_mes_eur=round((mes or 0.0) * cfg.precio_kwh_eur, 2),
        pico_horario_kw=round(d.pico_kw, 2) if d.pico_kw is not None else None,
        pico_momento=d.pico_momento,
        utilizacion_pct=utilizacion,
        potencia_recomendada_kw=recomendada,
        ahorro_potencia_eur_anio=ahorro,
        autoconsumo_12m_kwh=round(sum(d.autoconsumo.get(p, 0.0) for p in ultimos), 1),
        excedente_12m_kwh=round(sum(d.excedente.get(p, 0.0) for p in ultimos), 1),
        ultima_lectura=d.ultima,
        dias_sin_lectura=dias_sin,
        meses_con_datos=len(meses_validos),
        estado=estado,
    )


async def analizar(db: AsyncSession, hoy: date | None = None) -> Analisis:
    """Análisis completo (en caché hasta que cambie la última lectura o pasen 10 min)."""
    hoy = hoy or datetime.now(MADRID).date()
    ultima = await _ultima_lectura(db)
    clave = f"{hoy}|{ultima}"
    previo = _cache.get("analisis")
    if previo and previo.creado > time.monotonic() - CACHE_SEGUNDOS and clave in _cache:
        return previo
    sums = await suministros_reales(db)
    periodo = ultimo_mes_cerrado(hoy)
    inicio = mes_anterior(periodo, MESES_HISTORICO)
    desde = date(int(inicio[:4]), int(inicio[5:7]), 1)
    datos = await _datos_por_cups(db, [s.cups for s in sums], desde)
    ahora = datetime.now(UTC)
    filas = [fila_suministro(s, datos.get(s.cups), periodo, ahora) for s in sums]
    analisis = Analisis(hoy, periodo, sums, datos, filas, time.monotonic())
    _cache.clear()
    _cache["analisis"] = analisis
    _cache[clave] = analisis
    return analisis


def invalidar_cache() -> None:
    _cache.clear()


# ------------------------------------------------------------ resultados -----
def serie_mensual(
    a: Analisis, cups: set[str] | None = None, meses: int = 18
) -> list[MesConsumoEnergia]:
    tipos = {s.cups: tipo_de(s) for s in a.sums}
    periodos = [mes_anterior(a.periodo, i) for i in range(meses - 1, -2, -1)]  # + mes en curso
    salida = []
    for p in periodos:
        alum = edif = 0.0
        dias = []
        for c, d in a.datos.items():
            if cups is not None and c not in cups:
                continue
            kwh = d.meses.get(p, 0.0)
            if tipos.get(c) == "alumbrado":
                alum += kwh
            else:
                edif += kwh
            if p in d.dias_mes:
                dias.append(d.dias_mes[p])
        if not dias:
            continue
        completo = p <= a.periodo and max(dias) >= dias_del_mes(p) - 2
        salida.append(
            MesConsumoEnergia(
                periodo=p,
                kwh=round(alum + edif, 1),
                alumbrado_kwh=round(alum, 1),
                edificios_kwh=round(edif, 1),
                completo=completo,
            )
        )
    return salida


def recomendaciones(a: Analisis) -> list[RecomendacionEnergia]:
    recs: list[RecomendacionEnergia] = []
    revisar = sorted(
        (f for f in a.filas if f.ahorro_potencia_eur_anio),
        key=lambda f: -(f.ahorro_potencia_eur_anio or 0),
    )
    if revisar:
        ahorro = sum(f.ahorro_potencia_eur_anio or 0 for f in revisar)
        recs.append(
            RecomendacionEnergia(
                prioridad="alta" if ahorro >= 1000 else "media",
                titulo=f"Ajustar la potencia contratada de {suministros(len(revisar))}",
                detalle=(
                    "Su mayor consumo horario del último año no llega a la mitad de la "
                    "potencia contratada. Bajarla con un margen del 30 % ahorraría unos "
                    f"{miles(ahorro)} € al año en el término de potencia. Confirmar con el "
                    "maxímetro de la factura antes de pedir el cambio a la comercializadora."
                ),
                cups=[f.cups for f in revisar[:20]],
                ahorro_eur_anio=round(ahorro, 0),
            )
        )
    subidas = sorted(
        (
            f
            for f in a.filas
            if f.variacion_mes_pct is not None
            and f.variacion_mes_pct >= SUBIDA_ALERTA_PCT
            and f.consumo_mes_kwh - f.consumo_mes_anterior_kwh >= SUBIDA_ALERTA_KWH
        ),
        key=lambda f: -(f.consumo_mes_kwh - f.consumo_mes_anterior_kwh),
    )
    if subidas:
        top = subidas[0]
        recs.append(
            RecomendacionEnergia(
                prioridad="media",
                titulo=(
                    f"{suministros(len(subidas))} "
                    + ("consume" if len(subidas) == 1 else "consumen")
                    + " bastante más que el mes anterior"
                ),
                detalle=(
                    f"El mayor aumento es {top.direccion} ({top.cups}): "
                    f"{miles(top.consumo_mes_anterior_kwh)} → {miles(top.consumo_mes_kwh)} kWh "
                    f"(+{top.variacion_mes_pct:.0f} %). Revisar horarios, climatización o "
                    "una posible avería."
                ),
                cups=[f.cups for f in subidas[:20]],
            )
        )
    sin_datos = [f for f in a.filas if f.estado != "ok"]
    if sin_datos:
        recs.append(
            RecomendacionEnergia(
                prioridad="informativa",
                titulo=f"{suministros(len(sin_datos))} sin lecturas recientes en Datadis",
                detalle=(
                    f"No hay consumos de los últimos {DIAS_SIN_LECTURA} días. Puede ser un "
                    "contador sin telemedida, un suministro dado de baja o un retraso de la "
                    "distribuidora."
                ),
                cups=[f.cups for f in sin_datos[:20]],
            )
        )
    return recs


def resumen(a: Analisis) -> ResumenEnergiaMunicipal:
    cfg = get_settings()
    con_datos = [f for f in a.filas if f.estado != "sin_datos"]
    if not con_datos:
        return ResumenEnergiaMunicipal(
            hay_datos=False,
            suministros_total=len(a.filas),
            notas=[
                "Aún no hay lecturas de Datadis privado: carga los suministros con "
                "`python -m nijar_dti.workers.datadis_carga --solo privado`."
            ],
        )
    serie = serie_mensual(a)
    mes = next((m for m in serie if m.periodo == a.periodo), None)
    previo = next((m for m in serie if m.periodo == mes_anterior(a.periodo)), None)
    anio = next((m for m in serie if m.periodo == mes_anterior(a.periodo, 12)), None)
    consumo = mes.kwh if mes else 0.0
    ultimos = set(_ultimos_12(a.periodo))
    consumo_12m = sum(m.kwh for m in serie if m.periodo in ultimos)
    por_tarifa: dict[str, int] = defaultdict(int)
    for f in a.filas:
        por_tarifa[f.tarifa or "Sin dato"] += 1
    revisar = [f for f in a.filas if f.ahorro_potencia_eur_anio]
    ultima = max((f.ultima_lectura for f in a.filas if f.ultima_lectura), default=None)
    notas = [
        "Coste estimado con "
        + f"{cfg.precio_kwh_eur:.3f}".replace(".", ",")
        + " €/kWh (Datadis no facilita facturas).",
        "El pico horario es el mayor consumo en una hora (kW medios de esa hora); el maxímetro "
        "de 15 minutos de la factura puede ser algo mayor.",
    ]
    if anio is None:
        notas.append("Sin interanual: aún no hay 12 meses de lecturas de ese mes.")
    return ResumenEnergiaMunicipal(
        hay_datos=True,
        periodo=a.periodo,
        suministros_total=len(a.filas),
        suministros_con_datos=len(con_datos),
        suministros_alumbrado=sum(1 for f in a.filas if f.tipo == "alumbrado"),
        suministros_edificios=sum(1 for f in a.filas if f.tipo != "alumbrado"),
        consumo_mes_kwh=round(consumo, 1),
        consumo_mes_alumbrado_kwh=mes.alumbrado_kwh if mes else 0.0,
        consumo_mes_edificios_kwh=mes.edificios_kwh if mes else 0.0,
        variacion_mes_pct=variacion(consumo, previo.kwh if previo else None),
        variacion_interanual_pct=variacion(consumo, anio.kwh if anio else None),
        coste_mes_eur=round(consumo * cfg.precio_kwh_eur, 0),
        precio_kwh_eur=cfg.precio_kwh_eur,
        co2_mes_t=round(consumo * cfg.factor_co2_kwh_kg / 1000, 1),
        consumo_12m_kwh=round(consumo_12m, 0),
        coste_12m_eur=round(consumo_12m * cfg.precio_kwh_eur, 0),
        potencia_contratada_total_kw=round(sum(f.potencia_contratada_kw or 0 for f in a.filas), 1),
        contratos_a_revisar=len(revisar),
        ahorro_potencia_eur_anio=round(sum(f.ahorro_potencia_eur_anio or 0 for f in revisar), 0),
        autoconsumo_12m_kwh=round(sum(f.autoconsumo_12m_kwh for f in a.filas), 0),
        excedente_12m_kwh=round(sum(f.excedente_12m_kwh for f in a.filas), 0),
        cups_con_autoconsumo=sum(
            1 for f in a.filas if f.autoconsumo_12m_kwh > 0 or f.excedente_12m_kwh > 0
        ),
        sin_datos_recientes=sum(1 for f in a.filas if f.estado != "ok"),
        ultima_lectura=ultima,
        serie_mensual=serie,
        por_tarifa=dict(sorted(por_tarifa.items())),
        top_consumo=sorted(con_datos, key=lambda f: -f.consumo_mes_kwh)[:8],
        recomendaciones=recomendaciones(a),
        notas=notas,
    )


def filtrar(
    filas: list[SuministroAnalisis],
    tipo: str | None = None,
    buscar: str | None = None,
    orden: str = "consumo",
) -> list[SuministroAnalisis]:
    salida = filas
    if tipo == "alumbrado":
        salida = [f for f in salida if f.tipo == "alumbrado"]
    elif tipo == "edificios":
        salida = [f for f in salida if f.tipo != "alumbrado"]
    elif tipo == "revisar":
        salida = [f for f in salida if f.ahorro_potencia_eur_anio]
    elif tipo == "autoconsumo":
        salida = [f for f in salida if f.autoconsumo_12m_kwh > 0 or f.excedente_12m_kwh > 0]
    elif tipo == "sin_datos":
        salida = [f for f in salida if f.estado != "ok"]
    if buscar:
        b = buscar.strip().lower()
        salida = [f for f in salida if b in f.cups.lower() or b in f.direccion.lower()]
    claves = {
        "consumo": lambda f: -f.consumo_mes_kwh,
        "variacion": lambda f: -(f.variacion_mes_pct if f.variacion_mes_pct is not None else -1e9),
        "ahorro": lambda f: -(f.ahorro_potencia_eur_anio or 0),
        "utilizacion": lambda f: f.utilizacion_pct if f.utilizacion_pct is not None else 1e9,
        "cups": lambda f: f.cups,
        "direccion": lambda f: f.direccion.lower(),
    }
    return sorted(salida, key=claves.get(orden, claves["consumo"]))


async def detalle(db: AsyncSession, cups: str) -> DetalleSuministroEnergia | None:
    a = await analizar(db)
    cups = cups.strip().upper()
    s = next((x for x in a.sums if x.cups == cups), None)
    fila = next((f for f in a.filas if f.cups == cups), None)
    if s is None or fila is None:
        return None
    meta = s.metadatos if isinstance(s.metadatos, dict) else {}
    # perfil por hora del día de los últimos 30 días (laborables y festivos)
    hace30 = datetime.now(UTC) - timedelta(days=30)
    hora = _hora_local()
    filas = (
        await db.execute(
            select(hora, ConsumoHorarioEnergia.consumo_kwh).where(
                ConsumoHorarioEnergia.cups == cups, ConsumoHorarioEnergia.momento >= hace30
            )
        )
    ).all()
    suma: dict[str, list[float]] = {"lab": [0.0] * 24, "fest": [0.0] * 24, "todo": [0.0] * 24}
    cuenta: dict[str, list[int]] = {"lab": [0] * 24, "fest": [0] * 24, "todo": [0] * 24}
    for momento, kwh in filas:
        grupo = "fest" if es_dia_valle(momento.date()) else "lab"
        for g in (grupo, "todo"):
            suma[g][momento.hour] += float(kwh or 0)
            cuenta[g][momento.hour] += 1

    def media(g: str) -> list[float]:
        return [round(suma[g][h] / cuenta[g][h], 3) if cuenta[g][h] else 0.0 for h in range(24)]

    return DetalleSuministroEnergia(
        suministro=fila,
        contrato=_contrato(meta),
        distribuidora=meta.get("distribuidora"),
        codigo_postal=meta.get("codigo_postal"),
        serie_mensual=serie_mensual(a, {cups}, meses=24),
        perfil_horario_kwh=media("todo"),
        perfil_laborable_kwh=media("lab"),
        perfil_festivo_kwh=media("fest"),
    )


def csv_suministros(filas: list[SuministroAnalisis], periodo: str) -> str:
    """Listado de suministros en CSV («;» y coma decimal, para Excel en español)."""
    import csv
    import io

    def num(v: float | None, dec: int = 1) -> str:
        return "" if v is None else f"{v:.{dec}f}".replace(".", ",")

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        [
            "CUPS",
            "Dirección",
            "Tipo",
            "Tarifa",
            "Potencia contratada (kW)",
            f"Consumo {periodo} (kWh)",
            "Consumo mes anterior (kWh)",
            "Variación (%)",
            "Consumo 12 meses (kWh)",
            "Coste estimado del mes (€)",
            "Pico horario (kW)",
            "Utilización (%)",
            "Potencia recomendada (kW)",
            "Ahorro estimado (€/año)",
            "Autoconsumo 12 meses (kWh)",
            "Excedentes 12 meses (kWh)",
            "Última lectura",
            "Estado",
        ]
    )
    for f in filas:
        w.writerow(
            [
                f.cups,
                f.direccion,
                f.tipo,
                f.tarifa or "",
                num(f.potencia_contratada_kw, 2),
                num(f.consumo_mes_kwh),
                num(f.consumo_mes_anterior_kwh),
                num(f.variacion_mes_pct),
                num(f.consumo_12m_kwh),
                num(f.coste_mes_eur, 2),
                num(f.pico_horario_kw, 2),
                num(f.utilizacion_pct),
                num(f.potencia_recomendada_kw, 1),
                num(f.ahorro_potencia_eur_anio, 0),
                num(f.autoconsumo_12m_kwh),
                num(f.excedente_12m_kwh),
                f.ultima_lectura.astimezone(MADRID).strftime("%d/%m/%Y %H:%M")
                if f.ultima_lectura
                else "",
                f.estado,
            ]
        )
    return "﻿" + buf.getvalue()


async def recomendaciones_direccion(db: AsyncSession) -> list[RecomendacionIA]:
    """Recomendaciones de energía para la Vista de Gobierno (si hay datos reales)."""
    a = await analizar(db)
    salida = []
    for r in recomendaciones(a):
        if r.prioridad == "informativa":
            continue
        salida.append(
            RecomendacionIA(
                titulo=r.titulo,
                area="Energía",
                justificacion=r.detalle,
                impacto=(
                    f"Ahorro estimado de {miles(r.ahorro_eur_anio)} € al año"
                    if r.ahorro_eur_anio
                    else "Evitar sobrecostes y detectar averías a tiempo"
                ),
                prioridad="alta" if r.prioridad == "alta" else "media",
                accion=(
                    "Revisar la lista en Energía municipal → Costes y contratos"
                    if r.ahorro_eur_anio
                    else "Revisar los suministros en Energía municipal → Suministros"
                ),
            )
        )
    return salida
