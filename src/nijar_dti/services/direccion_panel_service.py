"""Vista de Gobierno 2.0 — panel visual de cada módulo.

Compone, para cada módulo de la Vista de Gobierno (resumen municipal, las 7
verticales y recomendaciones IA), un ``PanelDireccion`` listo para pintar:
cabecera con el hallazgo principal, KPIs con tendencia y bloques (gráficos,
rankings, mapas de calor, medidores, mapa por núcleo, eventos…).

Reglas de la plataforma que se respetan aquí:

- **No se inventan datos.** Todo sale de la base de datos (verticales,
  histórico mensual, visitas, opiniones, contexto oficial, consumo de IA…).
  Si una fuente aún no está integrada, el bloque se marca como ``pendiente``
  y el KPI lleva origen ``integrar`` con valor «—».
- Cada indicador declara su **origen**: ``real`` (medido), ``estimado``
  (derivado con factores de ``config``), ``modelo`` (previsión) o
  ``integrar`` (fuente pendiente).
- Las previsiones mensuales usan un modelo estacional sencillo y
  reproducible (mismo mes del año anterior × tendencia reciente) con una
  banda del 80 % a partir del error del propio modelo en los últimos 12 meses.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.models.alumbrado import CuadroMando, Luminaria, ZonaAlumbrado
from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia, EnergiaMunicipioDiario
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.metrica_historica import MetricaHistorica
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.verticales import (
    CamaraCCTV,
    Contenedor,
    PuntoMovilidad,
    SectorAgua,
    SuministroEnergia,
)
from nijar_dti.models.visita import TipoVisita, Visita
from nijar_dti.schemas.direccion import (
    AnilloHero,
    BloquePanel,
    ChipHero,
    EstadoVertical,
    HeroPanel,
    KpiPanel,
    OrigenDato,
    PanelDireccion,
    RecomendacionIA,
    SentidoDelta,
    SerieGrafico,
)
from nijar_dti.services import (
    consumo_ia_service,
    dashboards_service,
    direccion_service,
    prediccion_service,
)

MODULOS = (
    "resumen",
    "turismo",
    "alumbrado",
    "agua",
    "residuos",
    "movilidad",
    "seguridad",
    "energia",
    "recomendaciones",
)

_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# Objetivos de referencia que el panel dibuja como línea o umbral.
OBJETIVO_RENDIMIENTO_AGUA = 85.0
UMBRAL_LLENADO = 80.0
UMBRAL_PARKING = 90.0
COSTE_AGUA_M3_EUR = 0.60  # coste medio de producción del m³ (estimación prudente)

# Ritmo de llenado medio por fracción (puntos % al día) para la previsión a 48 h.
_LLENADO_DIA = {"resto": 18.0, "envases": 22.0, "organica": 20.0, "papel": 12.0, "vidrio": 8.0}

# Coordenadas de núcleos de población (para situar sectores que no las traen).
_NUCLEOS: dict[str, tuple[float, float]] = {
    "níjar": (36.9656, -2.207),
    "san josé": (36.7597, -2.1064),
    "campohermoso": (36.8447, -2.1503),
    "san isidro": (36.8705, -2.1820),
    "rodalquilar": (36.8517, -2.0416),
    "las negras": (36.8797, -2.0),
    "la isleta": (36.8122, -2.0516),
    "los albaricoques": (36.872, -2.08),
    "presillas bajas": (36.8389, -2.1078),
    "fernán pérez": (36.8857, -2.0538),
    "el barranquete": (36.8545, -2.1756),
    "agua amarga": (36.9370, -1.9350),
}

_ESTADO_PEOR = {"verde": 0, "ambar": 1, "rojo": 2}
_MADRID = ZoneInfo("Europe/Madrid")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


# ============================================================ utilidades puras
def fmt_num(v: float | None, dec: int = 0) -> str:
    """Formato español: miles con punto y decimales con coma."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    txt = f"{v:,.{dec}f}"
    return txt.replace(",", "§").replace(".", ",").replace("§", ".")


def delta_pct(actual: float | None, anterior: float | None) -> float | None:
    """Variación porcentual (None si no se puede calcular)."""
    if actual is None or not anterior:
        return None
    return round((actual - anterior) / anterior * 100, 1)


def texto_delta(var: float | None, bajar_bueno: bool = False) -> tuple[str | None, SentidoDelta]:
    """Texto «+4,2 %» y si la variación es buena o mala para la gestión."""
    if var is None:
        return None, "neutro"
    signo = "+" if var > 0 else ("−" if var < 0 else "")
    txt = f"{signo}{fmt_num(abs(var), 1)} %"
    if abs(var) < 0.5:
        return txt, "neutro"
    bueno = (var < 0) if bajar_bueno else (var > 0)
    return txt, "bueno" if bueno else "malo"


def etiqueta_periodo(periodo: str) -> str:
    """'2026-03' → 'mar 26'."""
    return f"{_MESES[int(periodo[5:7]) - 1]} {periodo[2:4]}"


def siguiente_periodo(periodo: str, n: int = 1) -> str:
    y, m = int(periodo[:4]), int(periodo[5:7]) + n
    while m > 12:
        y, m = y + 1, m - 12
    return f"{y:04d}-{m:02d}"


def prever_mensual(
    valores: Sequence[float], horizonte: int = 3
) -> list[tuple[float, float, float]]:
    """Previsión mensual estacional con banda del 80 %.

    Para cada mes futuro: valor del mismo mes del año anterior × tendencia
    (suma de los 3 últimos meses frente a los mismos 3 del año anterior).
    La banda sale de la desviación del error relativo del mismo método al
    reproducir los últimos 12 meses. Devuelve ``[(valor, inferior, superior)]``;
    lista vacía si no hay al menos 15 meses de histórico.
    """
    v = [float(x) for x in valores]
    if len(v) < 15:
        return []

    def tendencia(hasta: int) -> float:
        actual = sum(v[hasta - 3 : hasta])
        previo = sum(v[hasta - 15 : hasta - 12])
        return actual / previo if previo else 1.0

    errores: list[float] = []
    for i in range(max(15, len(v) - 12), len(v)):
        estimado = v[i - 12] * tendencia(i)
        if v[i]:
            errores.append((v[i] - estimado) / v[i])
    sigma = statistics.pstdev(errores) if len(errores) > 1 else 0.05
    sigma = max(sigma, 0.02)

    t = tendencia(len(v))
    serie = list(v)
    salida: list[tuple[float, float, float]] = []
    for _ in range(horizonte):
        valor = serie[len(serie) - 12] * t
        margen = valor * 1.28 * sigma
        salida.append(
            (round(valor, 2), round(max(valor - margen, 0.0), 2), round(valor + margen, 2))
        )
        serie.append(valor)
    return salida


def cola_homogenea(puntos: Sequence[tuple[str, float]]) -> list[float]:
    """Valores del tramo final con el mismo origen que el último punto.

    La previsión nunca mezcla histórico de ejemplo con dato real capturado: si
    el tramo real aún no llega a 15 meses, ``prever_mensual`` no devuelve nada.
    """
    valores = [v for _, v in puntos]
    origenes = getattr(puntos, "origenes", None)
    if not origenes:
        return valores
    real = origenes[-1] != "ejemplo"
    i = len(origenes)
    while i > 0 and (origenes[i - 1] != "ejemplo") == real:
        i -= 1
    return valores[i:]


def serie_con_prevision(
    puntos: Sequence[tuple[str, float]], meses_historia: int, horizonte: int
) -> tuple[list[str], list[SerieGrafico]]:
    """Etiquetas y series (real, previsión y banda) de un histórico mensual."""
    hist = list(puntos)[-max(meses_historia, 1) :]
    prev = prever_mensual(cola_homogenea(puntos), horizonte)
    etiquetas = [etiqueta_periodo(p) for p, _ in hist]
    if prev and hist:
        ultimo = hist[-1][0]
        etiquetas += [etiqueta_periodo(siguiente_periodo(ultimo, i + 1)) for i in range(len(prev))]
    n_h, n_p = len(hist), len(prev)
    nulos_p: list[float | None] = [None] * n_p
    nulos_h: list[float | None] = [None] * (n_h - 1)
    series = [
        SerieGrafico(
            nombre="Real",
            valores=[round(v, 2) for _, v in hist] + nulos_p,
            color="navy",
            relleno=True,
        )
    ]
    if prev and hist:
        ult = round(hist[-1][1], 2)
        series += [
            SerieGrafico(
                nombre="Previsión",
                valores=nulos_h + [ult] + [p[0] for p in prev],
                color="blue",
                discontinua=True,
                rol="prevision",
            ),
            SerieGrafico(
                nombre="Intervalo inferior",
                valores=nulos_h + [ult] + [p[1] for p in prev],
                color="blue",
                rol="banda_inf",
            ),
            SerieGrafico(
                nombre="Intervalo 80 %",
                valores=nulos_h + [ult] + [p[2] for p in prev],
                color="blue",
                rol="banda_sup",
            ),
        ]
    return etiquetas, series


def comparativa_anual(
    puntos: Sequence[tuple[str, float]], escala: float = 1.0, enlazar: bool = True
) -> tuple[list[str], list[SerieGrafico], int]:
    """Barras/linea «año actual frente al anterior» por mes, con previsión
    de los meses que faltan hasta diciembre. Devuelve también el año."""
    if not puntos:
        return list(_MESES), [], date.today().year
    anio = int(puntos[-1][0][:4])
    por_mes: dict[tuple[int, int], float] = {
        (int(p[:4]), int(p[5:7])): v * escala for p, v in puntos
    }
    actual = [por_mes.get((anio, m)) for m in range(1, 13)]
    previo = [por_mes.get((anio - 1, m)) for m in range(1, 13)]
    ultimo_mes = int(puntos[-1][0][5:7])
    faltan = 12 - ultimo_mes
    prev = prever_mensual([v * escala for v in cola_homogenea(puntos)], faltan) if faltan else []
    prevision: list[float | None] = [None] * 12
    if prev:
        if enlazar:  # en líneas, la previsión arranca en el último dato real
            prevision[ultimo_mes - 1] = actual[ultimo_mes - 1]
        for i, p in enumerate(prev):
            prevision[ultimo_mes + i] = p[0]

    def r(xs: list[float | None]) -> list[float | None]:
        return [round(x, 1) if x is not None else None for x in xs]

    series = [
        SerieGrafico(nombre=str(anio - 1), valores=r(previo), color="muted"),
        SerieGrafico(nombre=str(anio), valores=r(actual), color="teal", relleno=True),
    ]
    if prev:
        series.append(
            SerieGrafico(
                nombre="Previsión",
                valores=r(prevision),
                color="gold",
                discontinua=True,
                rol="prevision",
            )
        )
    return list(_MESES), series, anio


def chispa(valores: Sequence[float], n: int = 10) -> list[float]:
    return [round(float(x), 2) for x in list(valores)[-n:]]


def estado_rendimiento(rend: float | None) -> str:
    if rend is None:
        return "verde"
    if rend < 75:
        return "rojo"
    return "ambar" if rend < OBJETIVO_RENDIMIENTO_AGUA else "verde"


def nucleo_de(nombre: str) -> tuple[float, float] | None:
    """Coordenadas aproximadas del núcleo al que pertenece un nombre de sector."""
    n = nombre.lower()
    if n.startswith("níjar") or n.startswith("nijar"):
        return _NUCLEOS["níjar"]
    for clave, coord in sorted(_NUCLEOS.items(), key=lambda kv: -len(kv[0])):
        if clave in n:
            return coord
    return None


def llenado_previsto(llenado: float, fraccion: str, horas: float) -> float:
    """Llenado esperado de un contenedor tras ``horas`` (modelo lineal, máx. 100)."""
    return min(100.0, llenado + _LLENADO_DIA.get(fraccion, 15.0) * horas / 24.0)


def kpi(
    etiqueta: str,
    valor: str,
    *,
    unidad: str | None = None,
    var: float | None = None,
    bajar_bueno: bool = False,
    delta: str | None = None,
    sentido: SentidoDelta = "neutro",
    detalle: str | None = None,
    origen: OrigenDato = "real",
    icono: str = "chart",
    color: str = "navy",
    color_valor: str | None = None,
    serie: Sequence[float] = (),
) -> KpiPanel:
    if var is not None:
        delta, sentido = texto_delta(var, bajar_bueno)
    return KpiPanel(
        etiqueta=etiqueta,
        valor=valor,
        unidad=unidad,
        delta=delta,
        sentido=sentido,
        detalle=detalle,
        origen=origen,
        icono=icono,
        color=color,
        color_valor=color_valor,
        serie=chispa(serie),
    )


def bloque_recs(area: str, ancho: int = 6, limite: int = 3) -> BloquePanel:
    return BloquePanel(
        tipo="recomendaciones", titulo="Recomendaciones", area=area, ancho=ancho, limite=limite
    )


def bloque_fuentes(items: list[tuple[str, OrigenDato]]) -> BloquePanel:
    return BloquePanel(
        tipo="fuentes",
        titulo="Fuentes de datos del módulo",
        ancho=8,
        items=[{"nombre": n, "origen": o} for n, o in items],
    )


def bloque_preguntas(preguntas: list[str]) -> BloquePanel:
    return BloquePanel(
        tipo="preguntas",
        titulo="Preguntas que responde",
        ancho=4,
        items=[{"texto": p} for p in preguntas],
    )


def pendiente(titulo: str, texto: str, ancho: int = 6) -> BloquePanel:
    return BloquePanel(tipo="pendiente", titulo=titulo, texto=texto, origen="integrar", ancho=ancho)


def frase_portada(estado_texto: str, n_alerta: int) -> str:
    if estado_texto == "critico":
        return "Hay servicios que requieren una decisión hoy"
    if estado_texto == "atencion" or n_alerta:
        if n_alerta:
            return f"Níjar funciona bien, con {n_alerta} {'área' if n_alerta == 1 else 'áreas'} en seguimiento"
        return "Níjar funciona bien, con aspectos en seguimiento"
    return "Níjar funciona hoy con normalidad"


# ============================================================== acceso a datos
class SerieHist(list[tuple[str, float]]):
    """Serie mensual (periodo, valor) que recuerda el origen de cada punto."""

    def __init__(self, puntos: Sequence[tuple[str, float]] = (), origenes: Sequence[str] = ()):
        super().__init__(puntos)
        self.origenes: list[str] = list(origenes) or ["ejemplo"] * len(self)


def _clase(origen: str) -> str:
    """«ejemplo» (seed de instalación) frente a «capturado» (dato real o derivado)."""
    return "ejemplo" if origen == "ejemplo" else "capturado"


def origen_serie(serie: Sequence[tuple[str, float]], base: OrigenDato = "real") -> OrigenDato:
    """Origen que muestra el panel para un dato tomado del último punto de la serie."""
    origenes = getattr(serie, "origenes", None)
    if not origenes:
        return base
    ultimo = origenes[-1]
    if ultimo == "ejemplo":
        return "ejemplo"
    if ultimo == "estimado" and base == "real":
        return "estimado"
    return base


def nota_serie(serie: Sequence[tuple[str, float]]) -> str | None:
    """Aclara al pie qué meses son dato real y cuáles histórico de ejemplo."""
    origenes = getattr(serie, "origenes", None)
    if not origenes or not serie:
        return None
    reales = [i for i, o in enumerate(origenes) if o != "ejemplo"]
    if not reales:
        return "Histórico de ejemplo de la instalación: se sustituye mes a mes por el dato real capturado"
    if len(reales) == len(origenes):
        return None
    return (
        f"Dato real desde {etiqueta_periodo(serie[reales[0]][0])}; "
        "los meses anteriores son histórico de ejemplo"
    )


def con_nota(pie: str | None, serie: Sequence[tuple[str, float]]) -> str | None:
    nota = nota_serie(serie)
    if not nota:
        return pie
    return f"{pie} · {nota}" if pie else nota


async def _historico(db: AsyncSession, vertical: str, indicador: str) -> SerieHist:
    filas = (
        await db.execute(
            select(MetricaHistorica.periodo, MetricaHistorica.valor, MetricaHistorica.origen)
            .where(MetricaHistorica.vertical == vertical, MetricaHistorica.indicador == indicador)
            .order_by(MetricaHistorica.periodo)
        )
    ).all()
    return SerieHist([(str(p), float(v)) for p, v, _ in filas], [str(o) for _, _, o in filas])


def _yoy(puntos: Sequence[tuple[str, float]]) -> float | None:
    """Variación frente al mismo mes del año anterior (nunca mezcla ejemplo y dato real)."""
    if len(puntos) < 13:
        return None
    origenes = getattr(puntos, "origenes", None)
    if origenes and _clase(origenes[-1]) != _clase(origenes[-13]):
        return None
    return delta_pct(puntos[-1][1], puntos[-13][1])


async def _todas(db: AsyncSession, modelo: Any) -> list[Any]:
    return list((await db.execute(select(modelo))).scalars().all())


async def _zonas(db: AsyncSession) -> dict[str, ZonaAlumbrado]:
    return {z.id: z for z in await _todas(db, ZonaAlumbrado)}


def _sem(semaforo: list[EstadoVertical], clave: str) -> EstadoVertical | None:
    return next((s for s in semaforo if s.clave == clave), None)


_FRASE = {
    "verde": "Funciona con normalidad",
    "ambar": "Necesita seguimiento",
    "rojo": "Requiere una decisión",
}


def _hero(
    fondo: str,
    sem: EstadoVertical | None,
    titulo: str,
    subtitulo: str,
    chips: list[tuple[str, str]],
    anillo: AnilloHero | None,
) -> HeroPanel:
    return HeroPanel(
        fondo=fondo,
        estado=sem.estado if sem else None,
        frase=_FRASE.get(sem.estado) if sem else None,
        titulo=titulo,
        subtitulo=subtitulo,
        chips=[ChipHero(valor=v, etiqueta=e) for v, e in chips],
        anillo=anillo,
    )


async def _eventos_proximos(db: AsyncSession, limite: int = 4) -> list[EventoTuristico]:
    ahora = datetime.now(UTC)
    filas = (
        await db.execute(
            select(EventoTuristico)
            .where(
                EventoTuristico.publicado.is_(True),
                EventoTuristico.activo.is_(True),
                EventoTuristico.fecha_fin >= ahora,
                EventoTuristico.urn.notin_(urns_eventos_demo()),
            )
            .order_by(EventoTuristico.fecha_inicio)
            .limit(limite)
        )
    ).scalars()
    return list(filas)


def _item_evento(e: EventoTuristico, derecha: str | None = None) -> dict[str, Any]:
    d = e.fecha_inicio
    return {
        "dia": d.day,
        "mes": _MESES[d.month - 1],
        "titulo": e.nombre,
        "detalle": e.ubicacion or e.direccion or str(e.tipo),
        "derecha": derecha
        if derecha is not None
        else (f"{fmt_num(e.capacidad_aforo)} pers." if e.capacidad_aforo else ""),
    }


# ============================================================ RESUMEN MUNICIPAL
async def panel_resumen(db: AsyncSession) -> PanelDireccion:
    s = get_settings()
    r = await direccion_service.resumen_municipal(db)
    k = await direccion_service._kpis(db)
    alum = k["alumbrado"]

    # Gasto eléctrico municipal mensual = facturación de edificios + alumbrado × precio
    hist_edif = await _historico(db, "energia", "coste_eur")
    hist_alum = await _historico(db, "alumbrado", "consumo_kwh")
    coste_edif, kwh_alum = dict(hist_edif), dict(hist_alum)
    org_edif = dict(zip([p for p, _ in hist_edif], hist_edif.origenes, strict=True))
    org_alum = dict(zip([p for p, _ in hist_alum], hist_alum.origenes, strict=True))
    coste_ener = SerieHist(
        [(p, coste_edif[p] + kwh_alum.get(p, 0.0) * s.precio_kwh_eur) for p in sorted(coste_edif)],
        [
            "ejemplo" if "ejemplo" in (org_edif.get(p), org_alum.get(p, "ejemplo")) else "estimado"
            for p in sorted(coste_edif)
        ],
    )
    gasto_mes = coste_ener[-1][1] if coste_ener else None

    # afluencia: suma de la previsión de los próximos 7 días frente a los 7 últimos
    pred = await prediccion_service.prediccion_afluencia(db, "totem", horizonte_dias=7)
    prevista = sum(p.valor_estimado for p in pred.puntos)
    hasta = datetime.now(UTC)
    ultimos = await prediccion_service._serie_diaria(db, "totem", hasta - timedelta(days=6), hasta)
    real_7 = sum(p.valor for p in ultimos)

    hist_por_vertical = {
        "alumbrado": await _historico(db, "alumbrado", "consumo_kwh"),
        "agua": await _historico(db, "agua", "perdidas_m3"),
        "residuos": await _historico(db, "residuos", "toneladas"),
        "movilidad": await _historico(db, "movilidad", "accesos"),
        "seguridad": await _historico(db, "seguridad", "incidencias"),
        "energia": await _historico(db, "energia", "consumo_kwh"),
    }
    serie_totem = await dashboards_service.totems_usage_series(
        db, hasta - timedelta(days=30), hasta
    )
    puntos_totem = [float(p.total) for p in serie_totem.puntos]

    agua = k["agua"]
    res = k["residuos"]
    mov = k["movilidad"]
    seg = k["seguridad"]
    perdidas = hist_por_vertical["agua"][-1][1] if hist_por_vertical["agua"] else None
    tiles_valor = {
        "dti": (fmt_num(k["big_data"].menciones_ultimo_mes), "menciones en 30 días"),
        "alumbrado": (
            f"{fmt_num(kwh_alum[max(kwh_alum)] * s.precio_kwh_eur)} €" if kwh_alum else "—",
            "coste del último mes",
        ),
        "agua": (
            f"{fmt_num(perdidas * COSTE_AGUA_M3_EUR)} €"
            if perdidas
            else f"{agua.fugas_detectadas}",
            "pérdidas de red/mes" if perdidas else "fugas activas",
        ),
        "residuos": (f"{fmt_num(res.llenado_alto)}", "contenedores ≥ 80 %"),
        "movilidad": (f"{fmt_num(mov.ocupacion_parking_pct)} %", "ocupación de parkings"),
        "seguridad": (f"{fmt_num(seg.pct_online)} %", "cámaras online"),
        "energia": (
            f"{fmt_num(coste_edif[max(coste_edif)])} €" if coste_edif else "—",
            "coste del último mes",
        ),
    }
    id_tile = {"dti": "turismo"}
    tiles: list[dict[str, Any]] = []
    for sv in r.semaforo:
        idm = id_tile.get(sv.clave, sv.clave)
        serie = (
            puntos_totem
            if sv.clave == "dti"
            else [v for _, v in hist_por_vertical.get(sv.clave, [])]
        )
        valor, etq = tiles_valor.get(sv.clave, ("", ""))
        tiles.append(
            {
                "id": idm,
                "nombre": sv.nombre,
                "estado": sv.estado,
                "frase": _FRASE[sv.estado],
                "indicador": sv.indicador_clave,
                "valor": valor,
                "valor_etiqueta": etq,
                "serie": chispa(serie, 12),
            }
        )

    # mapa por núcleo: peor estado de alumbrado, residuos y cámaras de cada zona
    zonas = await _zonas(db)
    peor: dict[str, str] = dict.fromkeys(zonas, "verde")
    motivo: dict[str, list[str]] = defaultdict(list)
    for lum in await _todas(db, Luminaria):
        if lum.estado in ("averia", "sin_comunicacion") and lum.zona_id in peor:
            peor[lum.zona_id] = max(peor[lum.zona_id], "ambar", key=lambda e: _ESTADO_PEOR[e])
            if "alumbrado" not in motivo[lum.zona_id]:
                motivo[lum.zona_id].append("alumbrado")
    llenos = Counter(
        c.zona_id for c in await _todas(db, Contenedor) if (c.llenado_pct or 0) >= UMBRAL_LLENADO
    )
    for zid, n in llenos.items():
        if zid in peor and n >= 8:
            peor[zid] = max(peor[zid], "ambar", key=lambda e: _ESTADO_PEOR[e])
            motivo[zid].append("residuos")
    for cam in await _todas(db, CamaraCCTV):
        if cam.estado != "operativo" and cam.zona_id in peor:
            peor[cam.zona_id] = "rojo"
            motivo[cam.zona_id].append("cámara")
    puntos_mapa = [
        {
            "nombre": z.nombre,
            "lat": float(z.latitud),
            "lon": float(z.longitud),
            "estado": peor[zid],
            "texto": " · ".join(motivo[zid]) if motivo[zid] else "todo en verde",
        }
        for zid, z in zonas.items()
        if z.latitud is not None and z.longitud is not None
    ]

    # gasto energético por uso (suministros por tipo + alumbrado)
    gasto_tipo: dict[str, float] = defaultdict(float)
    for su in await _todas(db, SuministroEnergia):
        gasto_tipo[(su.tipo or "otros").capitalize()] += float(su.coste_mes_eur)
    gasto_tipo["Alumbrado público"] += (
        kwh_alum[max(kwh_alum)] if kwh_alum else alum.consumo_mes_kwh
    ) * s.precio_kwh_eur
    orden_gasto = sorted(gasto_tipo.items(), key=lambda kv: -kv[1])
    paleta = ["navy", "blue", "teal", "violet", "gold", "sky", "coral"]

    eventos = await _eventos_proximos(db)
    etq_coste, series_coste = serie_con_prevision(coste_ener, 24, 3)

    n_alerta = len(r.areas_alerta)
    hoy = datetime.now(UTC)
    dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    superior = (
        f"Ayuntamiento de Níjar · Smart City · {dias_es[hoy.weekday()]}, {hoy.day} de "
        f"{['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'][hoy.month - 1]}"
    )
    var_af = delta_pct(prevista, real_7)
    bloques: list[BloquePanel] = [
        BloquePanel(
            tipo="servicios",
            titulo="Los servicios del municipio, de un vistazo",
            subtitulo="Toca un servicio para abrir su panel",
            items=tiles,
        ),
        BloquePanel(
            tipo="linea",
            titulo="Gasto eléctrico municipal: 24 meses y previsión",
            subtitulo="Facturación mensual de los suministros municipales y previsión a 3 meses",
            origen=origen_serie(coste_ener),
            ancho=8,
            alto=270,
            etiquetas=etq_coste,
            series=series_coste,
            unidad="€",
            pie=con_nota(
                "Histórico mensual de la plataforma · previsión estacional con intervalo del 80 %",
                coste_ener,
            ),
        ),
        BloquePanel(
            tipo="recomendaciones",
            titulo="Decisiones pendientes",
            subtitulo="Las de mayor prioridad",
            ancho=4,
            limite=2,
            pie="Ver todas en Recomendaciones IA",
        ),
        BloquePanel(
            tipo="eventos",
            titulo="Esta semana en Níjar",
            subtitulo="Agenda del destino",
            ancho=4,
            items=[_item_evento(e) for e in eventos],
        ),
        BloquePanel(
            tipo="vivo",
            titulo="Tiempo, playas y Parque",
            subtitulo="Open-Meteo · ThingsBoard · en tiempo real",
            ancho=4,
            items=[
                {"medidor": "parkings", "valor": mov.ocupacion_parking_pct},
                {"medidor": "contenedores", "valor": res.llenado_medio_pct},
            ],
        ),
        BloquePanel(
            tipo="mapa",
            titulo="Estado por núcleo",
            subtitulo="Peor estado de sus servicios",
            ancho=4,
            items=puntos_mapa,
        ),
        BloquePanel(
            tipo="donut",
            titulo="¿En qué se va el gasto eléctrico?",
            subtitulo=f"{fmt_num(sum(gasto_tipo.values()))} € este mes · edificios y alumbrado",
            origen="real",
            ancho=6,
            alto=230,
            etiquetas=[n for n, _ in orden_gasto],
            series=[
                SerieGrafico(
                    nombre="Gasto",
                    valores=[round(v, 0) for _, v in orden_gasto],
                    colores=[paleta[i % len(paleta)] for i in range(len(orden_gasto))],
                )
            ],
            unidad="€",
        ),
    ]
    if r.interanual_turismo:
        bloques.append(
            BloquePanel(
                tipo="barras_h",
                titulo="Turismo frente al año pasado",
                subtitulo="Variación interanual · fuentes oficiales",
                origen="real",
                ancho=6,
                alto=230,
                etiquetas=[x.nombre for x in r.interanual_turismo],
                series=[
                    SerieGrafico(
                        nombre="Variación",
                        valores=[x.variacion_pct for x in r.interanual_turismo],
                        colores=[
                            "teal" if x.variacion_pct >= 0 else "coral"
                            for x in r.interanual_turismo
                        ],
                    )
                ],
                unidad="%",
                decimales=1,
                pie="INE, Junta de Andalucía, AENA · último periodo publicado",
            )
        )
    else:
        bloques.append(
            pendiente(
                "Turismo frente al año pasado",
                "Se mostrará al cargar las series oficiales (INE, Junta, AENA).",
                6,
            )
        )

    return PanelDireccion(
        modulo="resumen",
        titulo="Cuadro de Mando de Dirección · Smart City Níjar",
        intro="Visión ejecutiva de los servicios municipales: estado, coste, tendencia, lo que viene esta semana y las decisiones pendientes.",
        hero=HeroPanel(
            fondo="hero",
            superior=superior,
            titulo=frase_portada(r.estado_texto, n_alerta),
            subtitulo=(
                f"{r.servicios_ok} de {r.servicios_total} servicios municipales en correcto estado · "
                f"disponibilidad media del {fmt_num(r.disponibilidad_media_pct, 1)} %"
            ),
            chips=[
                ChipHero(
                    valor=f"{r.servicios_ok} / {r.servicios_total}", etiqueta="Servicios en verde"
                ),
                ChipHero(valor=str(r.incidencias_criticas), etiqueta="Incidencias críticas"),
                ChipHero(
                    valor=f"{fmt_num(r.satisfaccion_pct, 1)} %"
                    if r.satisfaccion_pct is not None
                    else "—",
                    etiqueta="Satisfacción ciudadana",
                ),
            ],
            anillo=AnilloHero(
                valor=str(r.estado_global),
                etiqueta="de 100",
                pct=r.estado_global,
                color={"correcto": "green", "atencion": "gold", "critico": "coral"}[r.estado_texto],
            ),
        ),
        kpis=[
            kpi(
                "Gasto eléctrico del mes",
                fmt_num(gasto_mes),
                unidad="€",
                var=_yoy(coste_ener),
                origen=origen_serie(coste_ener),
                bajar_bueno=True,
                detalle="edificios + alumbrado · último mes cerrado",
                icono="euro",
                serie=[v for _, v in coste_ener],
            ),
            kpi(
                "Ahorro estimado del mes",
                fmt_num(r.impacto.economico.ahorro_estimado_eur_mes),
                unidad="€",
                detalle="LED + autoconsumo",
                origen="estimado",
                icono="leaf",
                color="ok",
            ),
            kpi(
                "CO₂ evitado",
                fmt_num(r.co2_evitado_t_anio, 1),
                unidad="t/año",
                detalle=f"autoconsumo {fmt_num(r.impacto.ambiental.autoconsumo_pct)} %",
                origen="estimado",
                icono="leaf",
                color="teal",
            ),
            kpi(
                "Incidencias críticas",
                str(r.incidencias_criticas),
                detalle="abiertas en la plataforma",
                icono="alert",
                color="coral",
                color_valor="coral" if r.incidencias_criticas else None,
            ),
            kpi(
                "Satisfacción ciudadana",
                fmt_num(r.satisfaccion_pct, 1) if r.satisfaccion_pct is not None else "—",
                unidad="%" if r.satisfaccion_pct is not None else None,
                detalle=f"NPS {fmt_num(r.impacto.ciudadano.nps)}"
                if r.impacto.ciudadano.nps is not None
                else "NPS chatbot y tótems",
                icono="users",
                color="violet",
            ),
            kpi(
                "Afluencia prevista (7 días)",
                fmt_num(prevista),
                var=var_af,
                detalle="interacciones en tótems",
                origen="modelo",
                icono="turismo",
                color="blue",
                serie=puntos_totem,
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ===================================================================== TURISMO
async def panel_turismo(db: AsyncSession) -> PanelDireccion:
    s = get_settings()
    r = await direccion_service.resumen_municipal(db)
    sem = _sem(r.semaforo, "dti")
    big = await dashboards_service.big_data_overview(db)
    hasta = datetime.now(UTC)
    uso = await dashboards_service.totems_usage(db, hasta - timedelta(days=30), hasta)
    uso_prev = await dashboards_service.totems_usage(
        db, hasta - timedelta(days=60), hasta - timedelta(days=30)
    )
    pred = await prediccion_service.prediccion_afluencia(db, "totem", horizonte_dias=14)
    diaria = await prediccion_service._serie_diaria(db, "totem", hasta - timedelta(days=55), hasta)
    valores_d = [p.valor for p in diaria]
    fechas_d = [p.fecha for p in diaria]

    # semanas reales (8, la última son los 7 días hasta hoy) y previstas (2)
    semanas: list[tuple[str, float]] = []
    for fin in range(len(valores_d), 6, -7):
        f = fechas_d[fin - 7]
        semanas.insert(0, (f"{f.day} {_MESES[f.month - 1]}", sum(valores_d[fin - 7 : fin])))
    semanas = semanas[-8:]
    prev_sem: list[tuple[str, float, float, float]] = []
    for i in range(0, len(pred.puntos) - len(pred.puntos) % 7, 7):
        trozo = pred.puntos[i : i + 7]
        f0 = trozo[0].fecha
        prev_sem.append(
            (
                f"{f0.day} {_MESES[f0.month - 1]}",
                sum(p.valor_estimado for p in trozo),
                sum(p.banda_inferior for p in trozo),
                sum(p.banda_superior for p in trozo),
            )
        )
    etq = [w for w, _ in semanas] + [w for w, *_ in prev_sem]
    nh, npv = len(semanas), len(prev_sem)
    ult = semanas[-1][1] if semanas else None
    hueco: list[float | None] = [None] * max(nh - 1, 0)
    series_af = [
        SerieGrafico(
            nombre="Real",
            valores=[round(v) for _, v in semanas] + [None] * npv,
            color="muted",
            relleno=True,
        )
    ]
    if prev_sem and ult is not None:
        series_af += [
            SerieGrafico(
                nombre="Previsión",
                valores=hueco + [round(ult)] + [round(p[1]) for p in prev_sem],
                color="blue",
                discontinua=True,
                rol="prevision",
            ),
            SerieGrafico(
                nombre="Intervalo inferior",
                valores=hueco + [round(ult)] + [round(p[2]) for p in prev_sem],
                color="blue",
                rol="banda_inf",
            ),
            SerieGrafico(
                nombre="Intervalo 95 %",
                valores=hueco + [round(ult)] + [round(p[3]) for p in prev_sem],
                color="blue",
                rol="banda_sup",
            ),
        ]
    prox = prev_sem[0][1] if prev_sem else None
    var_prox = delta_pct(prox, ult)

    # idiomas, mapa de calor y recursos más consultados (visitas de tótems, 30 días)
    desde30 = hasta - timedelta(days=30)
    idiomas = (
        await db.execute(
            select(Visita.idioma, func.count())
            .where(Visita.ocurrido_en >= desde30, Visita.idioma.is_not(None))
            .group_by(Visita.idioma)
            .order_by(func.count().desc())
        )
    ).all()
    nombres_idioma = {
        "es": "Español",
        "en": "Inglés",
        "de": "Alemán",
        "fr": "Francés",
        "it": "Italiano",
    }
    total_id = sum(int(n) for _, n in idiomas) or 1
    top_id = [(nombres_idioma.get(str(i), str(i).upper()), int(n)) for i, n in idiomas[:5]]
    otros = total_id - sum(n for _, n in top_id)
    if otros > 0:
        top_id.append(("Otros", otros))
    pal_id = ["navy", "teal", "gold", "sky", "violet", "muted"]
    extranj = (
        round(100 * (total_id - sum(int(n) for i, n in idiomas if i == "es")) / total_id)
        if idiomas
        else None
    )

    desde28 = hasta - timedelta(days=28)
    visitas_t = (
        (
            await db.execute(
                select(Visita.ocurrido_en).where(
                    Visita.tipo == TipoVisita.INTERACCION_TOTEM, Visita.ocurrido_en >= desde28
                )
            )
        )
        .scalars()
        .all()
    )
    horas = list(range(9, 21))
    matriz = [[0.0] * len(horas) for _ in _DIAS]
    for t in visitas_t:
        lt = _aware(t).astimezone(_MADRID)
        h = lt.hour
        if 9 <= h <= 20:
            matriz[lt.weekday()][h - 9] += 1
    matriz = [[round(v / 4, 1) for v in fila] for fila in matriz]  # media semanal

    recursos = (
        await db.execute(
            select(RecursoTuristico.nombre, func.count())
            .select_from(Visita)
            .join(RecursoTuristico, RecursoTuristico.id == Visita.recurso_id)
            .where(Visita.ocurrido_en >= desde30)
            .group_by(RecursoTuristico.nombre)
            .order_by(func.count().desc())
            .limit(8)
        )
    ).all()

    # sentimiento semanal (opiniones, 8 semanas)
    desde8s = hasta - timedelta(weeks=8)
    ops = (
        await db.execute(
            select(Opinion.publicado_en, Opinion.score_sentimiento).where(
                Opinion.publicado_en >= desde8s, Opinion.score_sentimiento.is_not(None)
            )
        )
    ).all()
    por_semana: dict[int, list[float]] = defaultdict(list)
    for fecha, score in ops:
        sem_i = min(7, int((_aware(fecha) - desde8s).days // 7))
        por_semana[sem_i].append(float(score))
    sent_sem = [
        round(statistics.fmean(por_semana[i]), 2) if por_semana.get(i) else None for i in range(8)
    ]

    interanual = r.interanual_turismo
    por_clave = {x.clave: x for x in interanual}
    pern, aena = por_clave.get("pernoctaciones"), por_clave.get("pasajeros_aena")
    ia = await consumo_ia_service.resumen(db, desde30, hasta)
    coste_conv = (ia.coste_estimado_usd / ia.llamadas) if ia.llamadas else None
    origen_social: OrigenDato = "demo" if s.social_dry_run else "real"

    sent_txt = (
        f"{big.sentimiento_medio:+.2f}".replace(".", ",")
        if big.sentimiento_medio is not None
        else "—"
    )
    # La previsión solo encabeza el panel cuando el modelo supera su validación.
    if prox is not None and var_prox is not None and pred.cumple_umbral_mape:
        sube = "sube" if var_prox >= 0 else "baja"
        titulo = f"La afluencia prevista {sube} un {fmt_num(abs(var_prox), 0)} % la próxima semana"
    elif top_id:
        titulo = (
            f"{fmt_num(total_id)} consultas en tótems y chatbot en 30 días; "
            f"el {extranj} % en otro idioma"
        )
    else:
        titulo = "Afluencia, mercados y reputación del destino"

    bloques: list[BloquePanel] = [
        BloquePanel(
            tipo="linea",
            titulo="Afluencia semanal: real y previsión a 2 semanas",
            subtitulo="Interacciones en los tótems del destino por semana",
            origen="modelo",
            ancho=8,
            alto=290,
            etiquetas=etq,
            series=series_af,
            unidad="interacciones",
            pie=(
                f"Modelo estacional · error medio de validación {fmt_num(pred.mape_validacion, 1)} %"
                if pred.cumple_umbral_mape and pred.mape_validacion is not None
                else "Previsión orientativa: el modelo aún no tiene histórico suficiente para validarse"
            ),
        ),
        BloquePanel(
            tipo="donut",
            titulo="¿De dónde vienen?",
            subtitulo="Idioma de las consultas en tótems y chatbot (30 días)",
            origen="real",
            ancho=4,
            alto=190,
            etiquetas=[n for n, _ in top_id],
            series=[
                SerieGrafico(
                    nombre="Consultas",
                    valores=[float(v) for _, v in top_id],
                    colores=pal_id[: len(top_id)],
                )
            ],
            items=[
                {
                    "nombre": n,
                    "valor": round(100 * v / total_id),
                    "texto": f"{round(100 * v / total_id)} %",
                    "color": pal_id[i],
                }
                for i, (n, v) in enumerate(top_id[:4])
            ],
            unidad="consultas",
            pie="Proxy del mercado de origen hasta integrar GA4",
        )
        if top_id
        else pendiente("¿De dónde vienen?", "Aún no hay consultas registradas con idioma.", 4),
        BloquePanel(
            tipo="calor",
            titulo="¿Cuándo se usan los tótems? Día y hora",
            subtitulo="Media semanal de las 4 últimas semanas",
            origen="real",
            ancho=7,
            filas=_DIAS,
            columnas=[str(h) for h in horas],
            matriz=matriz,
            escala=["Menos", "Más"],
        ),
        BloquePanel(
            tipo="ranking",
            titulo="Lo más consultado en tótems y chatbot",
            subtitulo="Últimos 30 días · consultas por recurso",
            origen="real",
            ancho=5,
            items=[
                {"nombre": n, "valor": int(c), "color": "navy" if i < 3 else "teal"}
                for i, (n, c) in enumerate(recursos)
            ],
        )
        if recursos
        else pendiente("Lo más consultado", "Sin consultas a recursos en los últimos 30 días.", 5),
        BloquePanel(
            tipo="linea",
            titulo="Lo que se dice del destino",
            subtitulo="Sentimiento medio semanal (−1 a +1)",
            origen=origen_social,
            ancho=4,
            alto=170,
            etiquetas=[f"S{i + 1}" for i in range(8)],
            series=[
                SerieGrafico(nombre="Sentimiento", valores=sent_sem, color="teal", relleno=True)
            ],
            minimo=-1,
            maximo=1,
            decimales=2,
            items=[{"valor": t, "texto": "tema destacado"} for t in big.temas_top[:2]],
            pie="Social Listening (Meta y X)"
            + (" · datos de prueba hasta integrar los tokens" if s.social_dry_run else ""),
        ),
        BloquePanel(
            tipo="barras_h",
            titulo="Indicadores oficiales frente al año pasado",
            subtitulo="Variación interanual",
            origen="real",
            ancho=4,
            alto=250,
            etiquetas=[x.nombre.split(" (")[0] for x in interanual],
            series=[
                SerieGrafico(
                    nombre="Variación",
                    valores=[x.variacion_pct for x in interanual],
                    colores=["teal" if x.variacion_pct >= 0 else "coral" for x in interanual],
                )
            ],
            unidad="%",
            decimales=1,
        )
        if interanual
        else pendiente(
            "Indicadores oficiales", "Pendiente de cargar las series de INE, Junta y AENA.", 4
        ),
        bloque_recs("Turismo", ancho=4, limite=2),
        bloque_fuentes(
            [
                ("INE EOH · EGATUR · FRONTUR", "real"),
                ("Junta de Andalucía", "real"),
                ("AENA", "real"),
                ("ThingsBoard (aforo y banderas)", "real"),
                ("Tótems y chatbot", "real"),
                ("Modelo de afluencia", "modelo"),
                ("Meta (Facebook, Instagram) y X", origen_social),
                ("Google Analytics 4", "integrar"),
                ("App Vive Níjar", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Cuánta afluencia se espera la semana que viene?",
                "¿De qué mercados llegan los visitantes?",
                "¿Qué se dice del destino en redes?",
                "¿Dónde conviene reforzar la promoción?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="turismo",
        titulo="Turismo inteligente · Resumen de Dirección",
        intro="Afluencia, mercados de origen, lo que se dice del destino y lo que se espera las próximas semanas.",
        hero=_hero(
            "turismo",
            sem,
            titulo,
            "Previsión del modelo de afluencia de la plataforma, consultas en tótems y chatbot, y series oficiales de INE, Junta y AENA.",
            [
                (fmt_num(big.menciones_ultimo_mes), "Menciones/mes"),
                (sent_txt, "Sentimiento"),
                (fmt_num(uso.interacciones_total), "Usos de tótems (30 d)"),
                (fmt_num(uso.sesiones_unicas), "Sesiones únicas"),
            ],
            AnilloHero(
                valor=f"{extranj} %",
                etiqueta="consultas en otro idioma",
                pct=float(extranj),
                color="teal",
            )
            if extranj is not None
            else None,
        ),
        kpis=[
            kpi(
                "Afluencia prevista",
                fmt_num(prox),
                var=var_prox,
                detalle="próxima semana",
                origen="modelo",
                icono="users",
                color="blue",
                serie=[v for _, v in semanas],
            ),
            kpi(
                "Pernoctaciones",
                fmt_num(pern.valor) if pern else "—",
                var=pern.variacion_pct if pern else None,
                detalle=f"{pern.periodo} · INE EOH" if pern else "INE EOH",
                origen="real",
                icono="calendar",
                color="navy",
            ),
            kpi(
                "Pasajeros AENA",
                fmt_num(aena.valor) if aena else "—",
                var=aena.variacion_pct if aena else None,
                detalle=f"Almería · {aena.periodo}" if aena else "Aeropuerto de Almería",
                origen="real",
                icono="route",
                color="sky",
            ),
            kpi(
                "Usos de tótems",
                fmt_num(uso.interacciones_total),
                var=delta_pct(uso.interacciones_total, uso_prev.interacciones_total),
                detalle=f"{fmt_num(uso.sesiones_unicas)} sesiones únicas",
                origen="real",
                icono="present",
                color="violet",
                serie=valores_d[-30:],
            ),
            kpi(
                "Menciones en redes",
                fmt_num(big.menciones_ultimo_mes),
                detalle=f"sentimiento {sent_txt}",
                origen=origen_social,
                icono="chat",
                color="teal",
                serie=[x for x in sent_sem if x is not None],
            ),
            kpi(
                "Coste del chatbot IA",
                fmt_num(coste_conv, 3) if coste_conv is not None else "—",
                unidad="USD" if coste_conv is not None else None,
                detalle=f"por conversación · {fmt_num(ia.coste_estimado_usd, 2)} USD/mes",
                origen="real",
                icono="ai",
                color="gold",
                serie=[p.coste_estimado_usd for p in ia.serie_diaria],
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# =================================================================== ALUMBRADO
_DESCARGA = {"vsap", "hm"}  # lámparas de descarga: candidatas a renovar a LED


def _telegestion(cuadros: list[CuadroMando]) -> str:
    """Fabricante de telegestión declarado en el inventario (p. ej. "SOL-X")."""
    fabricantes = Counter(
        str((q.metadatos.get("telegestion") or {}).get("fabricante"))
        for q in cuadros
        if isinstance(q.metadatos, dict)
        and (q.metadatos.get("telegestion") or {}).get("fabricante")
    )
    return fabricantes.most_common(1)[0][0] if fabricantes else "punto a punto"


async def panel_alumbrado(db: AsyncSession) -> PanelDireccion:
    s = get_settings()
    k = await direccion_service._kpis(db)
    sem = direccion_service._semaforo_alumbrado(k["alumbrado"])
    o = k["alumbrado"]
    hist = await _historico(db, "alumbrado", "consumo_kwh")
    lums = await _todas(db, Luminaria)
    cuadros = await _todas(db, CuadroMando)
    zonas = await _zonas(db)

    # Consumo del último mes cerrado (el mismo dato que dibuja la gráfica);
    # el reparto por tecnología sale del consumo registrado de cada luminaria.
    consumo_mes = hist[-1][1] if hist else o.consumo_mes_kwh
    coste_mes = consumo_mes * s.precio_kwh_eur
    f = s.baseline_consumo_vsap_factor
    kwh_tec: dict[str, float] = defaultdict(float)
    for x in lums:
        kwh_tec[str(x.tecnologia)] += float(x.consumo_mes_kwh or 0)
    total_tec = sum(kwh_tec.values()) or 1.0
    led_kwh = consumo_mes * kwh_tec["led"] / total_tec
    ahorro_mes = led_kwh * (f - 1) * s.precio_kwh_eur
    # Inventario real de WeLight sin telegestión: los estados no se conocen aún.
    real_sin_tele = o.fuente_inventario == "welight" and not o.telemetria
    # Ahorro anual de renovar a LED cada luminaria de descarga (VSAP y halogenuro
    # metálico): su consumo (escalado al real del mes) × (1 − 1/f).
    escala = consumo_mes / total_tec
    ahorro_kwh_zona: dict[str, float] = defaultdict(float)
    for x in lums:
        if x.tecnologia in _DESCARGA:
            ahorro_kwh_zona[x.zona_id] += float(x.consumo_mes_kwh or 0) * escala
    factor_ahorro = 12 * (1 - 1 / f) * s.precio_kwh_eur
    pendientes = sum(1 for x in lums if x.tecnologia in _DESCARGA)
    prev = prever_mensual(cola_homogenea(hist), 1)

    etq_c, series_c, anio = comparativa_anual(hist, escala=0.001, enlazar=False)
    for se in series_c:
        if se.nombre == str(anio):
            se.color = "gold"
            se.relleno = False
        elif se.rol == "prevision":
            se.color = "navy"

    por_zona_vsap = sorted(
        (
            (zonas[z].nombre if z in zonas else z, n, ahorro_kwh_zona[z] * factor_ahorro)
            for z, n in Counter(x.zona_id for x in lums if x.tecnologia in _DESCARGA).items()
        ),
        key=lambda kv: -kv[2],
    )
    averias = Counter(x.zona_id for x in lums if x.estado == "averia")
    sincom = Counter(x.zona_id for x in lums if x.estado == "sin_comunicacion")
    zonas_inc = sorted({*averias, *sincom}, key=lambda z: -(averias[z] + sincom[z]))[:6]
    cuadros_alarma = [c for c in cuadros if c.alarmas or c.estado != "operativo"]
    yoy = _yoy(hist)

    tele = _telegestion(cuadros)
    cups_alumbrado = {
        c for q in cuadros if isinstance(q.metadatos, dict) for c in q.metadatos.get("cups") or []
    }
    por_nucleo = Counter(x.zona_id for x in lums)
    led_nucleo = Counter(x.zona_id for x in lums if x.tecnologia == "led")
    top_nucleos = [z for z, _ in por_nucleo.most_common(10)]
    bloque_nucleos = BloquePanel(
        tipo="barras_h",
        titulo="Puntos de luz por núcleo",
        subtitulo=f"Los 10 núcleos con más luminarias de {fmt_num(len(por_nucleo))}",
        origen="real",
        ancho=6,
        alto=300,
        apilado=True,
        etiquetas=[zonas[z].nombre if z in zonas else z for z in top_nucleos],
        series=[
            SerieGrafico(
                nombre="LED", valores=[float(led_nucleo[z]) for z in top_nucleos], color="gold"
            ),
            SerieGrafico(
                nombre="Otras tecnologías",
                valores=[float(por_nucleo[z] - led_nucleo[z]) for z in top_nucleos],
                color="navy",
            ),
        ],
        unidad="luminarias",
    )

    pct_led = o.pct_led
    bloques = [
        BloquePanel(
            tipo="barras",
            titulo=f"Consumo mensual: {anio} frente a {anio - 1}",
            subtitulo="MWh por mes · previsión de los meses que faltan",
            origen=origen_serie(hist),
            ancho=8,
            alto=290,
            etiquetas=etq_c,
            series=series_c,
            unidad="MWh",
            decimales=1,
            pie=con_nota("Histórico mensual de la plataforma · previsión estacional", hist),
        ),
        BloquePanel(
            tipo="donut",
            titulo="Parque de luminarias",
            subtitulo=f"{fmt_num(o.total_luminarias)} puntos de luz",
            origen="real",
            ancho=4,
            alto=180,
            etiquetas=["LED", "VSAP", "Solar"] + (["Otras"] if o.otras else []),
            series=[
                SerieGrafico(
                    nombre="Luminarias",
                    valores=[o.led, o.vsap, o.solar] + ([o.otras] if o.otras else []),
                    colores=["gold", "navy", "teal"] + (["sky"] if o.otras else []),
                )
            ],
            unidad="luminarias",
            items=[
                {"valor": fmt_num(pendientes), "texto": "VSAP/HM por renovar"},
                {"valor": f"{fmt_num(o.potencia_instalada_kw)} kW", "texto": "potencia instalada"},
                {"valor": fmt_num(o.cuadros_total), "texto": "cuadros de mando"}
                if real_sin_tele
                else {
                    "valor": f"{o.cuadros_online} / {o.cuadros_total}",
                    "texto": "cuadros online",
                },
                {"valor": fmt_num(len(cups_alumbrado)), "texto": "CUPS de alumbrado"}
                if real_sin_tele
                else {"valor": fmt_num(o.circuitos_total), "texto": "circuitos"},
            ],
            pie="Otras = halogenuro metálico o tecnología sin dato en el inventario"
            if o.otras
            else None,
        ),
        BloquePanel(
            tipo="ranking",
            titulo="Dónde invertir primero",
            subtitulo="Luminarias VSAP/HM por zona y ahorro anual de renovarlas a LED",
            origen="estimado",
            ancho=6,
            items=[
                {
                    "nombre": n,
                    "valor": c,
                    "texto": f"{c} · {fmt_num(a)} €/año",
                    "color": "navy" if i < 3 else "sky",
                }
                for i, (n, c, a) in enumerate(por_zona_vsap[:6])
            ],
            pie="Ahorro = consumo de esas luminarias × (1 − 1/factor LED) × precio del kWh",
        ),
        bloque_nucleos
        if real_sin_tele
        else BloquePanel(
            tipo="barras_h",
            titulo="Luminarias con problemas por zona",
            subtitulo=f"{o.en_averia} en avería y {o.sin_comunicacion} sin comunicación",
            origen="real",
            ancho=6,
            alto=230,
            apilado=True,
            etiquetas=[zonas[z].nombre if z in zonas else z for z in zonas_inc],
            series=[
                SerieGrafico(
                    nombre="En avería",
                    valores=[float(averias[z]) for z in zonas_inc],
                    color="coral",
                ),
                SerieGrafico(
                    nombre="Sin comunicación",
                    valores=[float(sincom[z]) for z in zonas_inc],
                    color="gold",
                ),
            ],
        )
        if zonas_inc
        else pendiente(
            "Luminarias con problemas", "No hay luminarias en avería ni sin comunicación.", 6
        ),
        pendiente(
            "Averías y alarmas de los cuadros",
            f"Llegarán al conectar la telegestión {tele} de los {fmt_num(o.cuadros_total)} "
            "cuadros: averías, pérdidas de comunicación y alarmas en tiempo real.",
            7,
        )
        if real_sin_tele
        else BloquePanel(
            tipo="eventos",
            titulo="Cuadros de mando con alarmas",
            subtitulo=f"{len(cuadros_alarma)} de {len(cuadros)} cuadros requieren revisión",
            origen="real",
            ancho=7,
            items=[
                {
                    "dia": c.codigo.split("-")[-1],
                    "mes": "cuadro",
                    "titulo": f"{c.nombre} · {zonas[c.zona_id].nombre if c.zona_id in zonas else c.zona_id}",
                    "detalle": ", ".join(c.alarmas or []) or c.estado.replace("_", " "),
                    "derecha": f"{fmt_num(c.potencia_kw, 1)} kW",
                }
                for c in cuadros_alarma[:6]
            ],
        )
        if cuadros_alarma
        else pendiente(
            "Cuadros de mando con alarmas", "Todos los cuadros funcionan sin alarmas.", 7
        ),
        bloque_recs("Alumbrado", ancho=5),
        pendiente(
            "Curva de encendido por cuadro",
            "Disponible al integrar la telegestión punto a punto o las curvas horarias de Datadis privado: detectará encendidos fuera de horario y regulación que no actúa.",
            12,
        ),
        bloque_fuentes(
            [
                (
                    "Inventario WeLight (luminarias y cuadros)"
                    if o.fuente_inventario == "welight"
                    else "Inventario de luminarias y cuadros",
                    "real",
                ),
                ("Histórico mensual de consumo", "real"),
                ("Precio del kWh y factor VSAP", "estimado"),
                ("Previsión estacional", "modelo"),
                (
                    f"Telegestión {tele}" if real_sin_tele else "Telegestión punto a punto",
                    "integrar",
                ),
                ("Datadis privado (curvas por cuadro)", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Cuánto cuesta el alumbrado y cuánto ahorra el LED?",
                "¿Qué zonas tienen más problemas?",
                "¿Dónde invertir primero y con qué ahorro?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="alumbrado",
        titulo="Alumbrado público · Resumen de Dirección",
        intro="Cuánto cuesta el alumbrado, cuánto ahorra el LED, dónde fallan los puntos de luz y dónde invertir en la siguiente fase.",
        hero=_hero(
            "alumbrado",
            sem,
            f"El LED ahorra {fmt_num(ahorro_mes)} € al mes; quedan {fmt_num(pendientes)} luminarias VSAP/HM por renovar",
            (
                f"Inventario WeLight: {fmt_num(o.total_luminarias)} puntos de luz en "
                f"{fmt_num(o.cuadros_total)} cuadros · telegestión {tele} pendiente de conectar"
                if real_sin_tele
                else f"{o.incidencias_abiertas} incidencias abiertas · {o.cuadros_alerta} cuadros en alerta"
            )
            + (
                f" · {por_zona_vsap[0][0]} concentra el mayor ahorro por renovar"
                if por_zona_vsap
                else ""
            ),
            [
                (fmt_num(o.total_luminarias), "Puntos de luz"),
                (fmt_num(o.cuadros_total), "Cuadros de mando"),
                (fmt_num(len(cups_alumbrado)), "CUPS de alumbrado"),
                (f"{fmt_num(o.potencia_instalada_kw)} kW", "Potencia instalada"),
            ]
            if real_sin_tele
            else [
                (f"{fmt_num(o.disponibilidad_pct, 1)} %", "Disponibilidad"),
                (str(o.incidencias_abiertas), "Incidencias abiertas"),
                (f"{o.cuadros_alerta} / {o.cuadros_total}", "Cuadros en alerta"),
                (f"{fmt_num(o.potencia_instalada_kw)} kW", "Potencia instalada"),
            ],
            AnilloHero(
                valor=f"{fmt_num(pct_led)} %", etiqueta="luminarias LED", pct=pct_led, color="gold"
            ),
        ),
        kpis=[
            kpi(
                "Coste del último mes",
                fmt_num(coste_mes),
                unidad="€",
                var=yoy,
                origen=origen_serie(hist),
                bajar_bueno=True,
                detalle=f"{etiqueta_periodo(hist[-1][0]) if hist else ''} · vs año anterior",
                icono="euro",
                serie=[v * s.precio_kwh_eur for _, v in hist],
            ),
            kpi(
                "Consumo del último mes",
                fmt_num(consumo_mes),
                unidad="kWh",
                var=yoy,
                origen=origen_serie(hist),
                bajar_bueno=True,
                detalle="red de alumbrado",
                icono="bolt",
                color="gold",
                serie=[v for _, v in hist],
            ),
            kpi(
                "Ahorro LED vs VSAP",
                fmt_num(ahorro_mes),
                unidad="€/mes",
                detalle=f"factor VSAP {fmt_num(f, 2)}",
                origen="estimado",
                icono="leaf",
                color="ok",
            ),
            *(
                [
                    kpi(
                        "Luminarias por renovar",
                        fmt_num(pendientes),
                        detalle=f"VSAP y halogenuro · {fmt_num(pendientes / (o.total_luminarias or 1) * 100, 1)} % del parque",
                        icono="wrench",
                        color="coral",
                    ),
                    kpi(
                        "Disponibilidad",
                        "—",
                        detalle=f"con la telegestión {tele}",
                        origen="integrar",
                        icono="bulb",
                        color="sky",
                    ),
                ]
                if real_sin_tele
                else [
                    kpi(
                        "Luminarias en avería",
                        fmt_num(o.en_averia),
                        detalle=f"{o.sin_comunicacion} sin comunicación",
                        icono="wrench",
                        color="coral",
                        color_valor="coral" if o.en_averia else None,
                    ),
                    kpi(
                        "Disponibilidad",
                        fmt_num(o.disponibilidad_pct, 1),
                        unidad="%",
                        detalle=f"{fmt_num(o.operativas)} operativas",
                        icono="bulb",
                        color="sky",
                    ),
                ]
            ),
            kpi(
                "Previsión del mes en curso",
                fmt_num(prev[0][0]) if prev else "—",
                unidad="kWh" if prev else None,
                var=delta_pct(prev[0][0], hist[-1][1]) if prev and hist else None,
                bajar_bueno=True,
                detalle="según estacionalidad" if prev else "con 15 meses de dato real",
                origen="ejemplo" if origen_serie(hist) == "ejemplo" else "modelo",
                icono="clock",
                color="violet",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ======================================================================== AGUA
async def panel_agua(db: AsyncSession) -> PanelDireccion:
    k = await direccion_service._kpis(db)
    o = k["agua"]
    sem = direccion_service._semaforo_agua(o)
    secs = sorted(await _todas(db, SectorAgua), key=lambda x: x.rendimiento_pct or 0)
    consumo = await _historico(db, "agua", "consumo_m3")
    perdidas = await _historico(db, "agua", "perdidas_m3")
    perd_mes = perdidas[-1][1] if perdidas else None
    bajo = [x for x in secs if (x.rendimiento_pct or 100) < OBJETIVO_RENDIMIENTO_AGUA]
    peor = secs[0] if secs else None
    etq_d, series_d = serie_con_prevision(consumo, 24, 3)
    prev = prever_mensual(cola_homogenea(consumo), 1)
    ratio = [
        (x.nombre, round(100 * float(x.caudal_nocturno_ls) / float(x.caudal_entrada_ls), 1))
        for x in secs
        if x.caudal_nocturno_ls is not None and x.caudal_entrada_ls
    ]
    ratio.sort(key=lambda kv: -kv[1])
    # Un punto por núcleo con el peor estado de sus sectores y su peor rendimiento.
    por_nucleo: dict[tuple[float, float], list[SectorAgua]] = defaultdict(list)
    for x in secs:
        c = nucleo_de(x.nombre)
        if c:
            por_nucleo[c].append(x)
    puntos = []
    for c, grupo in por_nucleo.items():
        estados = [
            "rojo" if x.fugas_detectadas else estado_rendimiento(x.rendimiento_pct) for x in grupo
        ]
        peor_s = min(grupo, key=lambda x: x.rendimiento_pct or 100)
        fugas = sum(x.fugas_detectadas for x in grupo)
        nombre = grupo[0].nombre if len(grupo) == 1 else grupo[0].nombre.split(" ")[0]
        if len(grupo) > 1 and nombre.lower() == "san":
            nombre = " ".join(grupo[0].nombre.split(" ")[:2])
        puntos.append(
            {
                "nombre": nombre,
                "lat": c[0],
                "lon": c[1],
                "estado": max(estados, key=lambda e: _ESTADO_PEOR[e]),
                "texto": f"{fmt_num(peor_s.rendimiento_pct)} %"
                + (f" · {len(grupo)} sectores" if len(grupo) > 1 else "")
                + (" · fuga" if fugas else ""),
            }
        )
    titulo = f"{len(bajo)} de {len(secs)} sectores no llegan al 85 % de rendimiento" + (
        f"; {peor.nombre} pierde el {fmt_num(100 - (peor.rendimiento_pct or 0))} %"
        if peor and peor.rendimiento_pct
        else ""
    )
    bloques = [
        BloquePanel(
            tipo="barras_h",
            titulo="Rendimiento de red por sector",
            subtitulo=f"Objetivo {fmt_num(OBJETIVO_RENDIMIENTO_AGUA)} % · en rojo, los sectores por debajo",
            origen="real",
            ancho=6,
            alto=max(240, 26 * len(secs)),
            etiquetas=[x.nombre for x in secs],
            series=[
                SerieGrafico(
                    nombre="Rendimiento",
                    valores=[round(x.rendimiento_pct or 0, 1) for x in secs],
                    colores=[
                        "coral" if (x.rendimiento_pct or 0) < OBJETIVO_RENDIMIENTO_AGUA else "teal"
                        for x in secs
                    ],
                )
            ],
            unidad="%",
            minimo=50,
            maximo=100,
            items=[
                {"nombre": "Bajo objetivo", "color": "coral"},
                {"nombre": "En objetivo", "color": "teal"},
            ],
        ),
        BloquePanel(
            tipo="barras_h",
            titulo="Caudal nocturno sobre caudal de entrada",
            subtitulo="Por encima del 50 % suele haber fugas ocultas",
            origen="real",
            ancho=6,
            alto=max(240, 26 * len(ratio)),
            etiquetas=[n for n, _ in ratio],
            series=[
                SerieGrafico(
                    nombre="Caudal nocturno",
                    valores=[v for _, v in ratio],
                    colores=["coral" if v >= 50 else "cyan" for _, v in ratio],
                )
            ],
            unidad="%",
            minimo=0,
            maximo=100,
        ),
        BloquePanel(
            tipo="linea",
            titulo="Consumo mensual de agua y previsión",
            subtitulo="m³ suministrados por mes · previsión a 3 meses con intervalo del 80 %",
            origen=origen_serie(consumo),
            ancho=8,
            alto=260,
            etiquetas=etq_d,
            series=series_d,
            unidad="m³",
            pie=con_nota(None, consumo),
        ),
        pendiente(
            "Nivel de depósitos y calidad del agua",
            "Disponible al integrar el SCADA de la concesionaria: nivel de cada depósito, cloro libre y turbidez en tiempo real.",
            4,
        ),
        BloquePanel(
            tipo="mapa",
            titulo="Rendimiento por sector",
            subtitulo="Estado de cada sector de la red",
            ancho=6,
            items=puntos,
        ),
        bloque_recs("agua"),
        bloque_fuentes(
            [
                ("Sectores, caudal y fugas", "real"),
                ("Inventario de contadores", "real"),
                ("Histórico mensual de consumo y pérdidas", "real"),
                ("Coste del m³", "estimado"),
                ("Previsión de demanda", "modelo"),
                ("Telelectura y facturación de la concesionaria", "integrar"),
                ("SCADA (depósitos y calidad)", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Cuánta agua perdemos y cuánto cuesta?",
                "¿Dónde hay fugas?",
                "¿Cómo evolucionará la demanda?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="agua",
        titulo="Ciclo del agua · Resumen de Dirección",
        intro="El agua que se pierde en la red y lo que cuesta, dónde están las fugas y cómo evolucionará la demanda.",
        hero=_hero(
            "agua",
            sem,
            titulo,
            f"{o.fugas_detectadas} sectores con fuga o consumo nocturno anómalo"
            + (
                f" · el caudal nocturno de {ratio[0][0]} es el {fmt_num(ratio[0][1])} % del de entrada"
                if ratio
                else ""
            ),
            [
                (str(o.fugas_detectadas), "Fugas activas"),
                (f"{fmt_num(perd_mes)} m³" if perd_mes else "—", "Pérdidas del mes"),
                (f"{fmt_num(o.pct_telelectura)} %", "Telelectura"),
                (f"{fmt_num(o.caudal_total_ls, 1)} l/s", "Caudal de entrada"),
            ],
            AnilloHero(
                valor=f"{fmt_num(o.rendimiento_medio_pct)} %",
                etiqueta=f"rendimiento · objetivo {fmt_num(OBJETIVO_RENDIMIENTO_AGUA)}",
                pct=o.rendimiento_medio_pct,
                color="gold" if o.rendimiento_medio_pct < OBJETIVO_RENDIMIENTO_AGUA else "green",
            ),
        ),
        kpis=[
            kpi(
                "Agua suministrada",
                fmt_num(consumo[-1][1]) if consumo else "—",
                unidad="m³",
                var=_yoy(consumo),
                origen=origen_serie(consumo),
                bajar_bueno=True,
                detalle="último mes",
                icono="drop",
                color="cyan",
                serie=[v for _, v in consumo],
            ),
            kpi(
                "Coste de las pérdidas",
                fmt_num(perd_mes * COSTE_AGUA_M3_EUR) if perd_mes else "—",
                unidad="€/mes",
                var=_yoy(perdidas),
                bajar_bueno=True,
                detalle=f"{fmt_num(perd_mes)} m³ no registrados" if perd_mes else "",
                origen=origen_serie(perdidas, "estimado"),
                icono="euro",
                color="coral",
                color_valor="coral",
                serie=[v for _, v in perdidas],
            ),
            kpi(
                "Rendimiento de red",
                fmt_num(o.rendimiento_medio_pct),
                unidad="%",
                detalle=f"objetivo {fmt_num(OBJETIVO_RENDIMIENTO_AGUA)} %",
                icono="gauge",
                color="navy",
            ),
            kpi(
                "Fugas activas",
                str(o.fugas_detectadas),
                detalle=f"{o.sectores_en_alerta} sectores en alerta",
                icono="alert",
                color="gold",
            ),
            kpi(
                "Telelectura",
                fmt_num(o.pct_telelectura),
                unidad="%",
                detalle=f"{fmt_num(o.contadores_telelectura)} de {fmt_num(o.contadores)} contadores",
                icono="chart",
                color="teal",
            ),
            kpi(
                "Demanda del mes en curso",
                fmt_num(prev[0][0]) if prev else "—",
                unidad="m³" if prev else None,
                var=delta_pct(prev[0][0], consumo[-1][1]) if prev and consumo else None,
                detalle="previsión estacional" if prev else "con 15 meses de dato real",
                origen="ejemplo" if origen_serie(consumo) == "ejemplo" else "modelo",
                icono="sun",
                color="violet",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ==================================================================== RESIDUOS
async def panel_residuos(db: AsyncSession) -> PanelDireccion:
    k = await direccion_service._kpis(db)
    o = k["residuos"]
    sem = direccion_service._semaforo_residuos(o)
    cont = await _todas(db, Contenedor)
    zonas = await _zonas(db)
    ton = await _historico(db, "residuos", "toneladas")
    con_s = [c for c in cont if c.tiene_sensor and c.llenado_pct is not None]
    riesgo48 = sum(
        1 for c in con_s if llenado_previsto(float(c.llenado_pct), str(c.fraccion), 24) >= 95
    )

    nombres_fr = {
        "resto": "Resto",
        "envases": "Envases",
        "papel": "Papel",
        "vidrio": "Vidrio",
        "organica": "Orgánica",
    }
    col_fr = {
        "resto": "#8A97B1",
        "envases": "gold",
        "papel": "blue",
        "vidrio": "ok",
        "organica": "brown",
    }
    por_fr: dict[str, list[float]] = defaultdict(list)
    for c in con_s:
        por_fr[str(c.fraccion)].append(float(c.llenado_pct))
    medidores = [
        {
            "nombre": nombres_fr.get(f, f),
            "valor": round(statistics.fmean(v)),
            "color": col_fr.get(f, "navy"),
        }
        for f, v in sorted(por_fr.items(), key=lambda kv: -statistics.fmean(kv[1]))
    ]

    franjas = [0, 8, 16, 24, 32, 40, 48]
    zonas_ids = sorted({c.zona_id for c in con_s}, key=lambda z: z)
    matriz: list[list[float]] = []
    for z in zonas_ids:
        cz = [c for c in con_s if c.zona_id == z]
        matriz.append(
            [
                round(
                    statistics.fmean(
                        llenado_previsto(float(c.llenado_pct), str(c.fraccion), h) for c in cz
                    ),
                    1,
                )
                for h in franjas[1:]
            ]
        )
    orden = sorted(range(len(zonas_ids)), key=lambda i: -matriz[i][-1])
    zonas_ids = [zonas_ids[i] for i in orden]
    matriz = [matriz[i] for i in orden]

    por_ruta = Counter(c.ruta for c in con_s if c.ruta and float(c.llenado_pct) >= UMBRAL_LLENADO)
    rutas = sorted({c.ruta for c in cont if c.ruta})
    riesgo_zona = Counter(
        c.zona_id
        for c in con_s
        if llenado_previsto(float(c.llenado_pct), str(c.fraccion), 48) >= 95
    )
    puntos = [
        {
            "nombre": z.nombre,
            "lat": float(z.latitud),
            "lon": float(z.longitud),
            "estado": "rojo"
            if riesgo_zona[zid] >= 15
            else ("ambar" if riesgo_zona[zid] >= 5 else "verde"),
            "texto": f"{riesgo_zona[zid]} en riesgo",
        }
        for zid, z in zonas.items()
        if z.latitud is not None and z.longitud is not None and zid in {c.zona_id for c in cont}
    ]
    etq_t, series_t = serie_con_prevision(ton, 24, 3)
    peor_z = (
        zonas[zonas_ids[0]].nombre
        if zonas_ids and zonas_ids[0] in zonas
        else (zonas_ids[0] if zonas_ids else "")
    )
    bloques = [
        BloquePanel(
            tipo="linea",
            titulo="Toneladas recogidas al mes y previsión",
            subtitulo="Total del municipio · el desglose por fracción llega con siGEUS",
            origen=origen_serie(ton),
            ancho=8,
            alto=290,
            etiquetas=etq_t,
            series=series_t,
            unidad="t",
            pie=con_nota(
                "Histórico mensual de la plataforma · previsión estacional con intervalo del 80 %",
                ton,
            ),
        ),
        BloquePanel(
            tipo="medidores",
            titulo="Llenado actual por fracción",
            subtitulo="Media de los contenedores con sensor",
            origen="real",
            ancho=4,
            items=medidores
            + [{"nombre": "Media", "valor": round(o.llenado_medio_pct), "color": "navy"}],
            pie=f"{fmt_num(o.total)} contenedores · {fmt_num(o.con_sensor)} con sensor de llenado",
        ),
        BloquePanel(
            tipo="calor",
            titulo="Llenado previsto en las próximas 48 horas",
            subtitulo="Media por zona · en rojo, por encima del 90 %",
            origen="modelo",
            ancho=7,
            filas=[zonas[z].nombre if z in zonas else z for z in zonas_ids],
            columnas=[f"+{h} h" for h in franjas[1:]],
            matriz=matriz,
            umbral=90,
            minimo=30,
            maximo=100,
            escala=["30 %", "100 %", "≥ 90 %"],
            pie="Llenado actual de los sensores + ritmo medio de llenado por fracción",
        ),
        BloquePanel(
            tipo="barras",
            titulo="Contenedores por encima del 80 % por ruta",
            subtitulo="Rutas que conviene adelantar",
            origen="real",
            ancho=5,
            alto=230,
            etiquetas=rutas,
            series=[
                SerieGrafico(
                    nombre="Contenedores ≥ 80 %",
                    valores=[float(por_ruta[r]) for r in rutas],
                    colores=["coral" if por_ruta[r] >= 10 else "teal" for r in rutas],
                )
            ],
        ),
        BloquePanel(
            tipo="mapa",
            titulo="Contenedores en riesgo por núcleo",
            subtitulo="Superarán el 95 % en 48 h si no se recogen",
            ancho=6,
            items=puntos,
        ),
        bloque_recs("Residuos"),
        bloque_fuentes(
            [
                ("Contenedores y sensores de llenado", "real"),
                ("Histórico mensual de toneladas", "real"),
                ("Previsión de llenado", "modelo"),
                ("siGEUS: recogidas por fracción y lavados", "integrar"),
                ("siGEUS: órdenes de trabajo y flota", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Cuánto recogemos?",
                "¿Qué contenedores se van a desbordar?",
                "¿Qué rutas conviene adelantar?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="residuos",
        titulo="Residuos · Resumen de Dirección",
        intro="Toneladas, llenado de contenedores y qué zonas se van a saturar en las próximas 48 horas.",
        hero=_hero(
            "residuos",
            sem,
            f"{fmt_num(o.llenado_alto)} contenedores superan el 80 %; {fmt_num(riesgo48)} llegarán al 95 % en 24 horas si no se recogen",
            f"{peor_z} es la zona con más llenado previsto. La recogida selectiva por fracción se verá al integrar siGEUS.",
            [
                (fmt_num(o.llenado_alto), "Contenedores ≥ 80 %"),
                (f"{fmt_num(o.llenado_medio_pct)} %", "Llenado medio"),
                (f"{fmt_num(ton[-1][1])} t" if ton else "—", "Recogidas el último mes"),
                (str(o.rutas), "Rutas"),
            ],
            AnilloHero(
                valor=f"{fmt_num(o.llenado_medio_pct)} %",
                etiqueta="llenado medio",
                pct=o.llenado_medio_pct,
                color="gold" if o.llenado_medio_pct >= 60 else "green",
            ),
        ),
        kpis=[
            kpi(
                "Toneladas del mes",
                fmt_num(ton[-1][1]) if ton else "—",
                unidad="t",
                var=_yoy(ton),
                origen=origen_serie(ton),
                bajar_bueno=True,
                detalle="vs mismo mes del año pasado",
                icono="trash",
                serie=[v for _, v in ton],
            ),
            kpi(
                "Llenado medio",
                fmt_num(o.llenado_medio_pct),
                unidad="%",
                detalle="contenedores con sensor",
                icono="gauge",
                color="teal",
            ),
            kpi(
                "Contenedores ≥ 80 %",
                fmt_num(o.llenado_alto),
                detalle="riesgo de desbordamiento",
                icono="alert",
                color="gold",
            ),
            kpi(
                "Llegarán al 95 % en 24 h",
                fmt_num(riesgo48),
                detalle="si no se adelanta la recogida",
                origen="modelo",
                icono="clock",
                color="coral",
                color_valor="coral" if riesgo48 else None,
            ),
            kpi(
                "Con sensor de llenado",
                fmt_num(o.pct_sensor),
                unidad="%",
                detalle=f"{fmt_num(o.con_sensor)} de {fmt_num(o.total)}",
                icono="chart",
                color="sky",
            ),
            kpi(
                "Recogida selectiva",
                "—",
                detalle="disponible con siGEUS",
                origen="integrar",
                icono="recycle",
                color="ok",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# =================================================================== MOVILIDAD
async def panel_movilidad(db: AsyncSession) -> PanelDireccion:
    k = await direccion_service._kpis(db)
    o = k["movilidad"]
    sem = direccion_service._semaforo_movilidad(o)
    pts = await _todas(db, PuntoMovilidad)
    accesos = await _historico(db, "movilidad", "accesos")
    parkings = sorted(
        [p for p in pts if p.tipo == "parking" and p.capacidad],
        key=lambda p: -(p.valor_actual or 0) / p.capacidad,
    )
    aforos = sorted([p for p in pts if p.tipo == "aforo"], key=lambda p: -(p.valor_actual or 0))
    recarga = [p for p in pts if p.tipo == "recarga_ev"]
    saturados = [p for p in parkings if 100 * (p.valor_actual or 0) / p.capacidad >= UMBRAL_PARKING]
    libres = o.plazas_totales - o.plazas_ocupadas
    etq_a, series_a = serie_con_prevision(accesos, 24, 3)
    col_e = {"operativo": "verde", "alerta": "ambar"}
    puntos = [
        {
            "nombre": p.nombre.replace("Parking ", "").replace("Aforo acceso ", ""),
            "lat": float(p.latitud),
            "lon": float(p.longitud),
            "estado": (
                "rojo"
                if 100 * (p.valor_actual or 0) / p.capacidad >= UMBRAL_PARKING
                else "ambar"
                if 100 * (p.valor_actual or 0) / p.capacidad >= 75
                else "verde"
            )
            if p.tipo == "parking" and p.capacidad
            else col_e.get(str(p.estado), "rojo"),
            "texto": f"{round(100 * (p.valor_actual or 0) / p.capacidad)} %"
            if p.tipo == "parking" and p.capacidad
            else (
                f"{p.valor_actual} {p.unidad or ''}".strip() if p.valor_actual is not None else ""
            ),
        }
        for p in pts
        if p.latitud is not None and p.longitud is not None and p.tipo in ("parking", "aforo")
    ]
    titulo = (
        f"{len(saturados)} {'aparcamiento' if len(saturados) == 1 else 'aparcamientos'} por encima del 90 %; la ocupación media es del {fmt_num(o.ocupacion_parking_pct)} %"
        if saturados
        else f"Los aparcamientos tienen margen: ocupación media del {fmt_num(o.ocupacion_parking_pct)} %"
    )
    bloques = [
        BloquePanel(
            tipo="ranking",
            titulo="Ocupación de aparcamientos ahora",
            subtitulo="Plazas ocupadas sobre capacidad",
            origen="real",
            ancho=4,
            items=[
                {
                    "nombre": p.nombre.replace("Parking ", ""),
                    "valor": round(100 * (p.valor_actual or 0) / p.capacidad),
                    "texto": f"{round(100 * (p.valor_actual or 0) / p.capacidad)} %",
                    "color": "coral"
                    if 100 * (p.valor_actual or 0) / p.capacidad >= UMBRAL_PARKING
                    else ("gold" if 100 * (p.valor_actual or 0) / p.capacidad >= 75 else "teal"),
                }
                for p in parkings
            ],
            maximo=100,
        ),
        BloquePanel(
            tipo="barras_h",
            titulo="Tráfico por acceso",
            subtitulo="Vehículos por hora ahora mismo",
            origen="real",
            ancho=4,
            alto=230,
            etiquetas=[p.nombre.replace("Aforo acceso ", "") for p in aforos],
            series=[
                SerieGrafico(
                    nombre="Tráfico",
                    valores=[float(p.valor_actual or 0) for p in aforos],
                    colores=["navy" if i == 0 else "sky" for i in range(len(aforos))],
                )
            ],
            unidad="veh/h",
        ),
        BloquePanel(
            tipo="mini",
            titulo="Recarga de vehículo eléctrico",
            subtitulo=f"{len(recarga)} puntos de recarga",
            origen="real",
            ancho=4,
            items=[
                {
                    "valor": f"{p.valor_actual or 0} / {p.capacidad or 0}",
                    "texto": p.nombre.replace("Recarga EV · ", "") + " · tomas libres",
                }
                for p in recarga[:4]
            ],
        ),
        BloquePanel(
            tipo="linea",
            titulo="Accesos al municipio por mes y previsión",
            subtitulo="Vehículos registrados por los aforos · previsión a 3 meses",
            origen=origen_serie(accesos),
            ancho=8,
            alto=270,
            etiquetas=etq_a,
            series=series_a,
            unidad="vehículos",
            pie=con_nota(None, accesos),
        ),
        pendiente(
            "Visitantes por núcleo y tiempo de estancia",
            "Disponible al integrar el WiFi público y los contadores de acceso al Parque (con evaluación de impacto de protección de datos).",
            4,
        ),
        BloquePanel(
            tipo="mapa",
            titulo="Aparcamientos y accesos",
            subtitulo="Ocupación y estado de cada punto",
            ancho=6,
            items=puntos,
        ),
        bloque_recs("Movilidad"),
        bloque_fuentes(
            [
                ("Aforos y aparcamientos", "real"),
                ("Puntos de recarga EV", "real"),
                ("Histórico mensual de accesos", "real"),
                ("Previsión de accesos", "modelo"),
                ("ThingsBoard (aforo del Parque)", "real"),
                ("WiFi público y contadores", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Dónde se concentran los vehículos?",
                "¿Hay saturación en los aparcamientos?",
                "¿Debe activarse algún aviso ciudadano?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="movilidad",
        titulo="Movilidad · Resumen de Dirección",
        intro="Dónde se concentran los vehículos, cómo están los aparcamientos de playa y cómo evolucionan los accesos.",
        hero=_hero(
            "movilidad",
            sem,
            titulo,
            (
                f"{', '.join(p.nombre.replace('Parking ', '') for p in saturados[:2])} al límite. "
                if saturados
                else ""
            )
            + f"{fmt_num(libres)} plazas libres en total.",
            [
                (f"{fmt_num(o.trafico_actual_veh_h)} veh/h", "Tráfico en accesos"),
                (fmt_num(libres), "Plazas libres"),
                (str(o.parkings), "Aparcamientos"),
                (f"{o.tomas_ev_libres}", "Tomas EV libres"),
            ],
            AnilloHero(
                valor=f"{fmt_num(o.ocupacion_parking_pct)} %",
                etiqueta="ocupación de parkings",
                pct=o.ocupacion_parking_pct,
                color="coral" if o.ocupacion_parking_pct >= UMBRAL_PARKING else "gold",
            ),
        ),
        kpis=[
            kpi(
                "Ocupación de parkings",
                fmt_num(o.ocupacion_parking_pct),
                unidad="%",
                detalle=f"{fmt_num(o.plazas_ocupadas)} de {fmt_num(o.plazas_totales)} plazas",
                icono="car",
                color="gold",
            ),
            kpi(
                "Aparcamientos ≥ 90 %",
                str(len(saturados)),
                detalle=f"de {len(parkings)} aparcamientos",
                icono="alert",
                color="coral",
                color_valor="coral" if saturados else None,
            ),
            kpi(
                "Tráfico en accesos",
                fmt_num(o.trafico_actual_veh_h),
                unidad="veh/h",
                detalle=f"{o.aforos} puntos de aforo",
                icono="route",
                color="navy",
            ),
            kpi(
                "Accesos del mes",
                fmt_num(accesos[-1][1]) if accesos else "—",
                var=_yoy(accesos),
                origen=origen_serie(accesos),
                detalle="vs mismo mes del año pasado",
                icono="chart",
                color="teal",
                serie=[v for _, v in accesos],
            ),
            kpi(
                "Tomas EV libres",
                f"{o.tomas_ev_libres}",
                detalle=f"{o.puntos_recarga_ev} puntos de recarga",
                icono="bolt",
                color="ok",
            ),
            kpi(
                "Visitantes por núcleo",
                "—",
                detalle="WiFi y contadores",
                origen="integrar",
                icono="users",
                color="violet",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# =================================================================== SEGURIDAD
def _riesgo_evento(e: EventoTuristico) -> tuple[str, str]:
    aforo = e.capacidad_aforo or 0
    if aforo >= 3000:
        return "critica", "Alto"
    if aforo >= 1000:
        return "alta", "Medio"
    return "media", "Bajo"


async def panel_seguridad(db: AsyncSession) -> PanelDireccion:
    k = await direccion_service._kpis(db)
    o = k["seguridad"]
    sem = direccion_service._semaforo_seguridad(o)
    cams = await _todas(db, CamaraCCTV)
    zonas = await _zonas(db)
    inc = await _historico(db, "seguridad", "incidencias")
    eventos = await _eventos_proximos(db, 4)
    tipos = Counter((c.tipo or "otra") for c in cams)
    nombres_t = {"fija": "Fija", "domo": "Domo", "lpr": "Lectura de matrículas"}
    por_zona: dict[str, list[CamaraCCTV]] = defaultdict(list)
    for c in cams:
        por_zona[c.zona_id].append(c)
    zonas_orden = sorted(
        por_zona,
        key=lambda z: (-sum(1 for c in por_zona[z] if c.estado != "operativo"), -len(por_zona[z])),
    )
    caidas = [c for c in cams if c.estado != "operativo"]
    lugar_caida = caidas[0].nombre if len(caidas) == 1 else None  # emplazamiento de la cámara
    etq_i, series_i = serie_con_prevision(inc, 24, 3)
    puntos = [
        {
            "nombre": zonas[z].nombre,
            "lat": float(zonas[z].latitud or 0.0),
            "lon": float(zonas[z].longitud or 0.0),
            "estado": "rojo" if any(c.estado != "operativo" for c in por_zona[z]) else "verde",
            "texto": f"{sum(1 for c in por_zona[z] if c.estado == 'operativo')} / {len(por_zona[z])}",
        }
        for z in por_zona
        if z in zonas and zonas[z].latitud is not None and zonas[z].longitud is not None
    ]
    titulo = (
        f"{o.online} de {o.camaras} cámaras operativas; {o.sin_comunicacion} sin comunicación"
        + (f" ({lugar_caida})" if lugar_caida else "")
        if o.sin_comunicacion
        else f"Las {o.camaras} cámaras de videovigilancia están operativas"
    )
    bloques = [
        BloquePanel(
            tipo="linea",
            titulo="Incidencias de seguridad por mes y previsión",
            subtitulo="Registradas en la plataforma · previsión a 3 meses",
            origen=origen_serie(inc),
            ancho=8,
            alto=270,
            etiquetas=etq_i,
            series=series_i,
            unidad="incidencias",
            pie=con_nota(None, inc),
        ),
        BloquePanel(
            tipo="donut",
            titulo="Cámaras por tipo",
            subtitulo=f"{o.camaras} cámaras · {o.con_analitica} con analítica",
            origen="real",
            ancho=4,
            alto=180,
            etiquetas=[nombres_t.get(t, t.capitalize()) for t in tipos],
            series=[
                SerieGrafico(
                    nombre="Cámaras",
                    valores=[float(n) for n in tipos.values()],
                    colores=["navy", "teal", "gold", "sky"][: len(tipos)],
                )
            ],
            unidad="cámaras",
        ),
        BloquePanel(
            tipo="ranking",
            titulo="Cámaras operativas por núcleo",
            subtitulo="En rojo, los núcleos con alguna cámara caída",
            origen="real",
            ancho=6,
            items=[
                {
                    "nombre": zonas[z].nombre if z in zonas else z,
                    "valor": round(
                        100
                        * sum(1 for c in por_zona[z] if c.estado == "operativo")
                        / len(por_zona[z])
                    ),
                    "texto": f"{sum(1 for c in por_zona[z] if c.estado == 'operativo')} / {len(por_zona[z])}",
                    "color": "coral"
                    if any(c.estado != "operativo" for c in por_zona[z])
                    else "teal",
                }
                for z in zonas_orden
            ],
            maximo=100,
        ),
        BloquePanel(
            tipo="eventos",
            titulo="Eventos con riesgo previsto",
            subtitulo="Agenda del destino × aforo esperado",
            origen="modelo",
            ancho=6,
            items=[
                {
                    **_item_evento(e, ""),
                    "prioridad": _riesgo_evento(e)[0],
                    "derecha_txt": _riesgo_evento(e)[1],
                }
                for e in eventos
            ],
        )
        if eventos
        else pendiente(
            "Eventos con riesgo previsto", "No hay eventos publicados en la agenda próxima.", 6
        ),
        BloquePanel(
            tipo="mapa",
            titulo="Cámaras por núcleo",
            subtitulo="Operativas sobre instaladas",
            ancho=6,
            items=puntos,
        ),
        bloque_recs("Seguridad"),
        bloque_fuentes(
            [
                ("Estado de las cámaras", "real"),
                ("Histórico mensual de incidencias", "real"),
                ("Agenda municipal", "real"),
                ("Riesgo por evento", "modelo"),
                ("Analítica de vídeo", "integrar"),
                ("Avisos 112 y Policía Local", "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Qué dispositivos están fuera de servicio?",
                "¿Cómo evolucionan las incidencias?",
                "¿Qué eventos requieren refuerzo?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="seguridad",
        titulo="Seguridad · Resumen de Dirección",
        intro="Cobertura de las cámaras, evolución de las incidencias y riesgo en los próximos eventos.",
        hero=_hero(
            "seguridad",
            sem,
            titulo,
            f"{o.con_analitica} cámaras con analítica · grabaciones conservadas {o.retencion_dias} días.",
            [
                (str(o.sin_comunicacion), "Sin comunicación"),
                (str(o.con_analitica), "Con analítica"),
                (fmt_num(inc[-1][1]) if inc else "—", "Incidencias del mes"),
                (f"{o.retencion_dias} d", "Retención"),
            ],
            AnilloHero(
                valor=f"{fmt_num(o.pct_online)} %",
                etiqueta="cámaras online",
                pct=o.pct_online,
                color="green" if o.pct_online >= 95 else "gold",
            ),
        ),
        kpis=[
            kpi(
                "Cámaras online",
                fmt_num(o.pct_online),
                unidad="%",
                detalle=f"{o.online} de {o.camaras}",
                icono="cam",
                color="ok",
            ),
            kpi(
                "Sin comunicación",
                str(o.sin_comunicacion),
                detalle="dispositivos a revisar",
                icono="alert",
                color="coral",
                color_valor="coral" if o.sin_comunicacion else None,
            ),
            kpi(
                "Con analítica",
                str(o.con_analitica),
                detalle="detección automática",
                icono="ai",
                color="violet",
            ),
            kpi(
                "Incidencias del mes",
                fmt_num(inc[-1][1]) if inc else "—",
                var=_yoy(inc),
                origen=origen_serie(inc),
                bajar_bueno=True,
                detalle="vs mismo mes del año pasado",
                icono="shield",
                color="blue",
                serie=[v for _, v in inc],
            ),
            kpi(
                "Retención",
                str(o.retencion_dias),
                unidad="días",
                detalle="grabaciones",
                icono="clock",
                color="navy",
            ),
            kpi(
                "Eventos de analítica",
                "—",
                detalle="aglomeración, intrusión",
                origen="integrar",
                icono="ai",
                color="gold",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ===================================================================== ENERGÍA
async def panel_energia(db: AsyncSession) -> PanelDireccion:
    s = get_settings()
    k = await direccion_service._kpis(db)
    o = k["energia"]
    sem = direccion_service._semaforo_energia(o)
    sums = await _todas(db, SuministroEnergia)
    consumo = await _historico(db, "energia", "consumo_kwh")
    coste = await _historico(db, "energia", "coste_eur")
    prev = prever_mensual(cola_homogenea(consumo), 1)
    yoy = _yoy(consumo)

    etq_c, series_c, anio = comparativa_anual(consumo, escala=0.001)
    por_tipo: dict[str, float] = defaultdict(float)
    for su in sums:
        por_tipo[(su.tipo or "otros").capitalize()] += float(su.consumo_mes_kwh)
    tipos = sorted(por_tipo.items(), key=lambda kv: -kv[1])
    pal = ["navy", "blue", "teal", "violet", "gold", "sky"]
    top = sorted(sums, key=lambda x: -float(x.consumo_mes_kwh))[:6]

    # curva horaria media (Datadis privado) y potencia sobredimensionada
    hace30 = datetime.now(UTC) - timedelta(days=30)
    horarias = (
        await db.execute(
            select(
                ConsumoHorarioEnergia.cups,
                ConsumoHorarioEnergia.momento,
                ConsumoHorarioEnergia.consumo_kwh,
            ).where(ConsumoHorarioEnergia.momento >= hace30)
        )
    ).all()
    curva: list[float] | None = None
    sobredim: int | None = None
    if horarias:
        acum: dict[int, list[float]] = defaultdict(list)
        maximo: dict[str, float] = defaultdict(float)
        por_hora_dia: dict[tuple[date, int], float] = defaultdict(float)
        for cups, momento, kwh in horarias:
            por_hora_dia[(momento.date(), momento.hour)] += float(kwh)
            maximo[str(cups)] = max(maximo[str(cups)], float(kwh))
        for (_, h), v in por_hora_dia.items():
            acum[h].append(v)
        curva = [round(statistics.fmean(acum[h]), 1) if acum.get(h) else 0.0 for h in range(24)]
        contratada = {su.cups: float(su.potencia_contratada_kw) for su in sums}
        sobredim = sum(
            1 for c, m in maximo.items() if contratada.get(c) and m < 0.6 * contratada[c]
        )

    # Datadis público: consumo del municipio por sector y mes (6 meses)
    filas_mun = (
        await db.execute(
            select(
                EnergiaMunicipioDiario.fecha,
                EnergiaMunicipioDiario.sector,
                EnergiaMunicipioDiario.energia_kwh,
            ).where(EnergiaMunicipioDiario.fecha >= date.today() - timedelta(days=190))
        )
    ).all()
    mun: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for fecha, sector, kwh in filas_mun:
        mun[f"{fecha.year:04d}-{fecha.month:02d}"][str(sector)] += float(kwh) / 1e6
    meses_mun = sorted(mun)[-6:]
    sectores = sorted(
        {sec for m in meses_mun for sec in mun[m]},
        key=lambda sec: -sum(mun[m].get(sec, 0) for m in meses_mun),
    )
    col_sec = ["ok", "navy", "teal", "muted", "gold", "violet"]

    ahorro_fv = o.autoconsumo_mes_kwh * s.precio_kwh_eur
    consumo_mes = consumo[-1][1] if consumo else o.consumo_mes_kwh
    coste_mes = coste[-1][1] if coste else o.coste_mes_eur
    mes_txt = etiqueta_periodo(consumo[-1][0]) if consumo else "mes en curso"
    co2_t = consumo_mes * s.factor_co2_kwh_kg / 1000
    if yoy is not None:
        mas_menos = "menos" if yoy < 0 else "más"
        titulo = f"Los edificios municipales consumen un {fmt_num(abs(yoy), 0)} % {mas_menos} que hace un año"
    else:
        titulo = "Consumo y coste de los edificios municipales"

    bloques = [
        BloquePanel(
            tipo="linea",
            titulo=f"Consumo mensual: {anio} frente a {anio - 1}",
            subtitulo="MWh por mes · previsión hasta diciembre",
            origen=origen_serie(consumo),
            ancho=8,
            alto=290,
            etiquetas=etq_c,
            series=series_c,
            unidad="MWh",
            decimales=1,
            pie=con_nota(
                "Histórico mensual de la plataforma (Datadis) · previsión estacional", consumo
            ),
        ),
        BloquePanel(
            tipo="donut",
            titulo="¿Quién consume?",
            subtitulo="Último mes por tipo de suministro",
            origen="real",
            ancho=4,
            alto=190,
            etiquetas=[n for n, _ in tipos],
            series=[
                SerieGrafico(
                    nombre="Consumo",
                    valores=[round(v) for _, v in tipos],
                    colores=pal[: len(tipos)],
                )
            ],
            items=[
                {
                    "nombre": n,
                    "valor": round(v),
                    "texto": f"{fmt_num(v / 1000, 1)} MWh",
                    "color": pal[i],
                }
                for i, (n, v) in enumerate(tipos[:4])
            ],
            unidad="kWh",
        ),
        BloquePanel(
            tipo="ranking",
            titulo="Los edificios que más consumen",
            subtitulo="Último mes · kWh y coste",
            origen="real",
            ancho=6,
            items=[
                {
                    "nombre": x.edificio,
                    "valor": round(float(x.consumo_mes_kwh)),
                    "texto": f"{fmt_num(x.consumo_mes_kwh)} · {fmt_num(x.coste_mes_eur)} €",
                    "color": "navy" if i < 3 else "sky",
                }
                for i, x in enumerate(top)
            ],
        ),
        BloquePanel(
            tipo="linea",
            titulo="Curva horaria media de los edificios",
            subtitulo="kWh por hora · media de los últimos 30 días",
            origen="real",
            ancho=6,
            alto=230,
            etiquetas=[f"{h}h" for h in range(24)],
            series=[
                SerieGrafico(nombre="Consumo", valores=list(curva), color="navy", relleno=True)
            ],
            unidad="kWh",
            decimales=1,
            pie="Datadis privado (curva horaria por CUPS)",
        )
        if curva
        else pendiente(
            "Curva horaria de los edificios",
            "Disponible al conectar el usuario de Datadis con autorización sobre los CUPS municipales: consumo hora a hora, consumo nocturno sin uso y potencia sobredimensionada.",
            6,
        ),
        BloquePanel(
            tipo="barras",
            titulo="Consumo eléctrico del municipio por sector",
            subtitulo="Datadis público · GWh por mes",
            origen="real",
            ancho=6,
            alto=240,
            apilado=True,
            etiquetas=[etiqueta_periodo(m) for m in meses_mun],
            series=[
                SerieGrafico(
                    nombre=sec.capitalize(),
                    valores=[round(mun[m].get(sec, 0.0), 2) for m in meses_mun],
                    color=col_sec[i % len(col_sec)],
                )
                for i, sec in enumerate(sectores[:6])
            ],
            unidad="GWh",
            decimales=2,
        )
        if meses_mun
        else pendiente(
            "Consumo del municipio por sector",
            "Se mostrará al cargar los datos públicos de Datadis.",
            6,
        ),
        bloque_recs("Energía"),
        bloque_fuentes(
            [
                ("Suministros por CUPS y coste", "real"),
                ("Datadis público (municipio por sector)", "real" if meses_mun else "integrar"),
                ("Autoconsumo fotovoltaico", "real"),
                ("Factor de emisión de CO₂", "estimado"),
                ("Previsión de consumo", "modelo"),
                ("Datadis privado (curvas horarias)", "real" if curva else "integrar"),
            ]
        ),
        bloque_preguntas(
            [
                "¿Qué edificios consumen más?",
                "¿Cuánto ahorra el autoconsumo?",
                "¿Dónde conviene invertir?",
            ]
        ),
    ]
    return PanelDireccion(
        modulo="energia",
        titulo="Energía municipal · Resumen de Dirección",
        intro="La factura eléctrica del Ayuntamiento, qué edificios la generan y cuánto se puede recortar con autoconsumo.",
        hero=_hero(
            "energia",
            sem,
            titulo,
            f"{o.edificios} edificios y {o.cups} suministros · {o.cups_con_fotovoltaica} con fotovoltaica."
            + (f" Previsión del mes en curso: {fmt_num(prev[0][0])} kWh." if prev else ""),
            [
                (f"{fmt_num(consumo_mes)} kWh", f"Consumo · {mes_txt}"),
                (f"{fmt_num(coste_mes)} €", f"Coste · {mes_txt}"),
                (f"{fmt_num(o.coste_medio_kwh, 3)} €", "Por kWh"),
                (f"{fmt_num(co2_t, 1)} t", "CO₂ del mes"),
            ],
            AnilloHero(
                valor=f"{fmt_num(o.autoconsumo_pct)} %",
                etiqueta="autoconsumo fotovoltaico",
                pct=min(100.0, o.autoconsumo_pct),
                color="green",
            ),
        ),
        kpis=[
            kpi(
                "Consumo del último mes",
                fmt_num(consumo_mes),
                unidad="kWh",
                var=yoy,
                origen=origen_serie(consumo),
                bajar_bueno=True,
                detalle=f"{mes_txt} · vs año anterior",
                icono="bolt",
                serie=[v for _, v in consumo],
            ),
            kpi(
                "Coste del último mes",
                fmt_num(coste_mes),
                unidad="€",
                var=_yoy(coste),
                origen=origen_serie(coste),
                bajar_bueno=True,
                detalle=f"{o.edificios} edificios",
                icono="euro",
                color="teal",
                serie=[v for _, v in coste],
            ),
            kpi(
                "Ahorro por autoconsumo",
                fmt_num(ahorro_fv),
                unidad="€/mes",
                detalle=f"{o.cups_con_fotovoltaica} CUPS con FV",
                icono="sun",
                color="gold",
            ),
            kpi(
                "Potencia sobredimensionada",
                str(sobredim) if sobredim is not None else "—",
                unidad="CUPS" if sobredim is not None else None,
                detalle="máximo < 60 % de lo contratado"
                if sobredim is not None
                else "con Datadis privado",
                origen="real" if sobredim is not None else "integrar",
                icono="gauge",
                color="coral",
            ),
            kpi(
                "Previsión del mes en curso",
                fmt_num(prev[0][0]) if prev else "—",
                unidad="kWh" if prev else None,
                var=delta_pct(prev[0][0], consumo[-1][1]) if prev and consumo else None,
                bajar_bueno=True,
                detalle="según estacionalidad" if prev else "con 15 meses de dato real",
                origen="ejemplo" if origen_serie(consumo) == "ejemplo" else "modelo",
                icono="clock",
                color="violet",
            ),
            kpi(
                "CO₂ emitido",
                fmt_num(co2_t, 1),
                unidad="t/mes",
                detalle=f"factor {fmt_num(s.factor_co2_kwh_kg, 2)} kg/kWh",
                origen="estimado",
                icono="leaf",
                color="ok",
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ============================================================ RECOMENDACIONES
def resumen_semanal(r: Any, recs: list[RecomendacionIA]) -> str:
    """Párrafo para Alcaldía con lo esencial de la semana (reglas, sin IA externa)."""
    partes = [
        f"El índice de ciudad está en {r.estado_global} sobre 100, con {r.servicios_ok} de {r.servicios_total} servicios en verde."
    ]
    if r.areas_alerta:
        partes.append("En seguimiento: " + ", ".join(a.lower() for a in r.areas_alerta) + ".")
    criticas = [x for x in recs if x.prioridad == "critica" and x.estado == "pendiente"]
    if criticas:
        partes.append(
            f"Hay {len(criticas)} decisión(es) crítica(s) pendiente(s): "
            + "; ".join(x.titulo.lower() for x in criticas[:2])
            + "."
        )
    partes.append(
        f"El ahorro estimado del mes es de {fmt_num(r.ahorro_estimado_eur_mes)} € y se evitan {fmt_num(r.co2_evitado_t_anio, 1)} t de CO₂ al año."
    )
    if r.incidencias_criticas:
        partes.append(
            f"Quedan {r.incidencias_criticas} incidencia(s) crítica(s) abierta(s) en la plataforma."
        )
    return " ".join(partes)


async def panel_recomendaciones(db: AsyncSession, recs: list[RecomendacionIA]) -> PanelDireccion:
    r = await direccion_service.resumen_municipal(db)
    hasta = datetime.now(UTC)
    ia = await consumo_ia_service.resumen(db, hasta - timedelta(days=30), hasta)
    estados = Counter(x.estado for x in recs)
    total = len(recs)
    aceptadas = estados["aceptada"] + estados["ejecutada"]
    pendientes = estados["pendiente"] + estados["en_revision"]
    criticas = sum(
        1 for x in recs if x.prioridad == "critica" and x.estado in ("pendiente", "en_revision")
    )
    por_area = Counter(x.area for x in recs)
    servicios = sorted(ia.por_servicio, key=lambda d: -d.coste_estimado_usd)
    pal = ["violet", "teal", "navy", "gold"]
    bloques = [
        BloquePanel(
            tipo="embudo",
            titulo="Embudo de decisiones",
            subtitulo="De la propuesta a la ejecución",
            origen="real",
            ancho=4,
            items=[
                {
                    "nombre": "Propuestas",
                    "valor": total,
                    "color": "#7C6BF0",
                    "texto": "por el motor de recomendaciones",
                },
                {
                    "nombre": "Aceptadas",
                    "valor": aceptadas,
                    "color": "#1A5FD0",
                    "texto": f"{round(100 * aceptadas / total) if total else 0} % de las propuestas",
                },
                {
                    "nombre": "Ejecutadas",
                    "valor": estados["ejecutada"],
                    "color": "#17A394",
                    "texto": f"{round(100 * estados['ejecutada'] / aceptadas) if aceptadas else 0} % de las aceptadas",
                },
            ],
            pie="Estados: pendiente, en revisión, aceptada, descartada y ejecutada",
        ),
        BloquePanel(
            tipo="barras",
            titulo="Recomendaciones por área",
            subtitulo="Dónde se concentran las propuestas actuales",
            origen="real",
            ancho=8,
            alto=250,
            etiquetas=[a for a, _ in por_area.most_common()],
            series=[
                SerieGrafico(
                    nombre="Recomendaciones",
                    valores=[float(n) for _, n in por_area.most_common()],
                    color="violet",
                )
            ],
        ),
        BloquePanel(
            tipo="recomendaciones",
            titulo="Decisiones",
            subtitulo="Acepta, pon en revisión o descarta; el estado queda registrado",
            ancho=8,
        ),
        BloquePanel(
            tipo="texto",
            titulo="Resumen semanal para Alcaldía",
            subtitulo=f"Generado el {hasta.day} de {['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'][hasta.month - 1]}",
            ancho=4,
            texto=resumen_semanal(r, recs),
            items=[
                {"valor": fmt_num(ia.llamadas), "texto": "Llamadas a la IA (30 días)"},
                {"valor": f"{fmt_num(ia.coste_estimado_usd, 2)} USD", "texto": "Coste de la IA"},
            ],
            etiquetas=[d.clave.capitalize() for d in servicios[:4]],
            series=[
                SerieGrafico(
                    nombre="Coste",
                    valores=[d.coste_estimado_usd for d in servicios[:4]],
                    colores=pal[: len(servicios[:4])],
                )
            ]
            if servicios
            else [],
            unidad="USD",
            decimales=2,
            pie="Consumo de IA: GET /dashboards/ia/consumo",
        ),
    ]
    return PanelDireccion(
        modulo="recomendaciones",
        titulo="Recomendaciones IA · Decisiones y seguimiento",
        intro="Cada recomendación con su justificación, impacto y acción, y su estado hasta la ejecución.",
        hero=HeroPanel(
            fondo="recomendaciones",
            superior="Recomendaciones IA · motor de reglas sobre los datos de la plataforma",
            titulo=(
                f"{pendientes} {'decisión pendiente' if pendientes == 1 else 'decisiones pendientes'}"
                + (f", {criticas} {'crítica' if criticas == 1 else 'críticas'}" if criticas else "")
            ),
            subtitulo=f"{aceptadas} aceptadas y {estados['ejecutada']} ejecutadas de {total} propuestas actuales.",
            chips=[
                ChipHero(valor=str(total), etiqueta="Propuestas"),
                ChipHero(valor=str(aceptadas), etiqueta="Aceptadas"),
                ChipHero(valor=str(estados["ejecutada"]), etiqueta="Ejecutadas"),
                ChipHero(valor=str(estados["descartada"]), etiqueta="Descartadas"),
            ],
            anillo=AnilloHero(
                valor=f"{round(100 * aceptadas / total) if total else 0} %",
                etiqueta="tasa de aceptación",
                pct=float(round(100 * aceptadas / total) if total else 0),
                color="violet",
            ),
        ),
        kpis=[
            kpi(
                "Pendientes de decidir",
                str(pendientes),
                detalle=f"{criticas} críticas",
                icono="bell",
                color="coral",
                color_valor="coral" if criticas else None,
            ),
            kpi(
                "Aceptadas",
                str(aceptadas),
                detalle=f"de {total} propuestas",
                icono="chart",
                color="blue",
            ),
            kpi(
                "Ejecutadas",
                str(estados["ejecutada"]),
                detalle="con seguimiento",
                icono="check",
                color="teal",
            ),
            kpi(
                "Descartadas",
                str(estados["descartada"]),
                detalle="con comentario de dirección",
                icono="alert",
                color="muted",
            ),
            kpi(
                "Coste de la IA",
                fmt_num(ia.coste_estimado_usd, 2),
                unidad="USD",
                detalle="últimos 30 días",
                icono="ai",
                color="violet",
                serie=[p.coste_estimado_usd for p in ia.serie_diaria],
            ),
            kpi(
                "Llamadas a la IA",
                fmt_num(ia.llamadas),
                detalle="chatbot y traducción · tokens por día",
                icono="users",
                color="navy",
                serie=[float(p.tokens) for p in ia.serie_diaria],
            ),
        ],
        bloques=bloques,
        generado_en=datetime.now(UTC),
    )


# ======================================================= DATOS DE DEMOSTRACIÓN
# Fuente del catálogo (fuentes_datos) que alimenta cada vertical técnica. Mientras
# su estado no sea «operativa», los datos de esa vertical son los de demostración
# cargados en la instalación y el panel los etiqueta como tales.
FUENTES_CONTEXTO = frozenset({"ine_eoh", "ine_egatur", "ine_frontur", "junta_andalucia", "aena"})
FUENTE_VERTICAL = {
    "alumbrado": "FD-008",
    "agua": "FD-009",
    "residuos": "FD-010",
    "movilidad": "FD-011",
    "seguridad": "FD-012",
    "energia": "FD-013",
}
_NOMBRE_VERTICAL = {
    "alumbrado": "Alumbrado público",
    "agua": "Ciclo del agua",
    "residuos": "Residuos",
    "movilidad": "Movilidad",
    "seguridad": "Seguridad",
    "energia": "Energía municipal",
}


def urns_eventos_demo() -> list[str]:
    """URN de los eventos de demostración de la instalación (no son agenda real)."""
    from nijar_dti.data.seeds.demo_data import generar_eventos_seed

    return [str(e["urn"]) for e in generar_eventos_seed()]


@dataclass
class EstadoDatos:
    """Qué datos del panel son reales y cuáles de demostración."""

    vertical_demo: dict[str, bool] = field(default_factory=dict)
    contexto_demo: bool = True  # alguna serie oficial (INE, Junta, AENA) sigue siendo sintética
    # Fuentes de contexto sin dato real; None = todas si ``contexto_demo``, ninguna si no.
    contexto_fuentes_demo: frozenset[str] | None = None
    social_demo: bool = True  # Social Listening en modo de prueba
    actividad_mixta: bool = False  # visitas, chatbot u opiniones de demo junto a las reales

    def demo(self, vertical: str) -> bool:
        return self.vertical_demo.get(vertical, True)

    def verticales_demo(self) -> list[str]:
        return [v for v in FUENTE_VERTICAL if self.demo(v)]

    def fuentes_contexto_demo(self) -> frozenset[str]:
        if self.contexto_fuentes_demo is not None:
            return self.contexto_fuentes_demo
        return FUENTES_CONTEXTO if self.contexto_demo else frozenset()


async def estado_datos(db: AsyncSession) -> EstadoDatos:
    from nijar_dti.models.contexto import ContextoTuristico
    from nijar_dti.models.faq import InteraccionChatbot
    from nijar_dti.models.fuente_dato import FuenteDato
    from nijar_dti.services.datadis_service import hay_suministros_reales
    from nijar_dti.services.inventario_alumbrado_service import fuente_inventario

    filas = (
        await db.execute(
            select(FuenteDato.codigo, FuenteDato.estado).where(
                FuenteDato.codigo.in_(list(FUENTE_VERTICAL.values()))
            )
        )
    ).all()
    operativas = {str(c) for c, e in filas if str(e) == "operativa"}
    demo = {v: cod not in operativas for v, cod in FUENTE_VERTICAL.items()}
    # Energía es real en cuanto hay suministros cargados desde Datadis (API o fichero).
    if await hay_suministros_reales(db):
        demo["energia"] = False
    # Alumbrado es real con el inventario de WeLight cargado; lo que aún no
    # tiene (telegestión) el propio panel lo muestra como pendiente de integrar.
    if await fuente_inventario(db) == "welight":
        demo["alumbrado"] = False

    con_dato_real = set(
        (
            await db.execute(
                select(ContextoTuristico.fuente)
                .where(
                    func.coalesce(ContextoTuristico.metadatos["sintetico"].as_string(), "false")
                    != "true"
                )
                .distinct()
            )
        ).scalars()
    )
    contexto_demo = FUENTES_CONTEXTO - {str(f) for f in con_dato_real}
    actividad_demo = (
        await db.execute(
            select(func.count()).where(InteraccionChatbot.sesion_id.like("demo-session-%"))
        )
    ).scalar_one() + (
        await db.execute(select(func.count()).where(Opinion.fuente_id_externo.like("demo-%")))
    ).scalar_one()
    return EstadoDatos(
        vertical_demo=demo,
        contexto_demo=bool(contexto_demo),
        contexto_fuentes_demo=frozenset(contexto_demo),
        social_demo=get_settings().social_dry_run,
        actividad_mixta=bool(actividad_demo),
    )


_A_DEMO = {"real", "estimado", "modelo"}
# Bloques y fuentes de una vertical que NO salen de sus datos de demostración.
_NO_VERTICALES = {
    "Eventos con riesgo previsto",
    "Agenda municipal",
    "Riesgo por evento",
    "Previsión estacional",
    "Previsión de demanda",
    "Previsión de llenado",
    "Previsión de accesos",
    "Previsión de consumo",
    "ThingsBoard (aforo del Parque)",
}


# KPIs y gráficos que salen del histórico mensual: ya llevan su propio origen
# (ejemplo, o dato real capturado de Datadis) y no dependen del inventario demo.
_HISTORICO = (
    "Coste del último mes",
    "Consumo del último mes",
    "Previsión del mes en curso",
    "Demanda del mes en curso",
    "Agua suministrada",
    "Coste de las pérdidas",
    "Toneladas del mes",
    "Accesos del mes",
    "Incidencias del mes",
    "Consumo mensual",
    "Toneladas recogidas al mes",
    "Accesos al municipio por mes",
    "Incidencias de seguridad por mes",
)


def _es_historico(nombre: str | None) -> bool:
    return bool(nombre) and str(nombre).startswith(_HISTORICO)


def _marcar_vertical_demo(panel: PanelDireccion, vertical: str) -> None:
    for k in panel.kpis:
        if k.origen in _A_DEMO and not _es_historico(k.etiqueta):
            k.origen = "demo"
    for b in panel.bloques:
        if b.titulo in _NO_VERTICALES or _es_historico(b.titulo):
            continue
        if b.origen in _A_DEMO:
            b.origen = "demo"
        if b.tipo == "fuentes":
            for it in b.items:
                if it.get("origen") in _A_DEMO and it.get("nombre") not in _NO_VERTICALES:
                    it["origen"] = "demo"
    panel.aviso = (
        f"Datos de demostración: {_NOMBRE_VERTICAL[vertical]} aún no está integrado con el "
        f"sistema municipal ({FUENTE_VERTICAL[vertical]}). Las cifras, estados y ubicaciones de "
        "esta pantalla son de ejemplo y no deben usarse para decidir."
    )


def _cambiar(panel: PanelDireccion, etiquetas: set[str], origen: OrigenDato) -> None:
    """Cambia el origen de los KPIs y bloques con esas etiquetas o títulos."""
    for k in panel.kpis:
        if k.etiqueta in etiquetas and k.origen != "ejemplo":
            k.origen = origen
    for b in panel.bloques:
        if b.titulo in etiquetas and b.origen != "ejemplo":
            b.origen = origen


def _cambiar_fuentes(panel: PanelDireccion, nombres: set[str], origen: OrigenDato) -> None:
    for b in panel.bloques:
        if b.tipo == "fuentes":
            for it in b.items:
                if it.get("nombre") in nombres:
                    it["origen"] = origen


# Qué series oficiales alimentan cada KPI, bloque o fila de "fuentes" del panel.
_CONTEXTO: dict[str, frozenset[str]] = {
    "Pernoctaciones": frozenset({"ine_eoh"}),
    "Pasajeros AENA": frozenset({"aena"}),
    "Indicadores oficiales frente al año pasado": FUENTES_CONTEXTO,
    "Indicadores oficiales": FUENTES_CONTEXTO,
    "Turismo frente al año pasado": FUENTES_CONTEXTO,
}
_FUENTES_CONTEXTO: dict[str, frozenset[str]] = {
    "INE EOH · EGATUR · FRONTUR": frozenset({"ine_eoh", "ine_egatur", "ine_frontur"}),
    "Junta de Andalucía": frozenset({"junta_andalucia"}),
    "AENA": frozenset({"aena"}),
}


def _origen_contexto(fuentes: frozenset[str], demo: frozenset[str]) -> OrigenDato | None:
    """``demo`` si todas sus series son sintéticas, ``mixto`` si solo algunas."""
    sinteticas = fuentes & demo
    if not sinteticas:
        return None
    return "demo" if sinteticas == fuentes else "mixto"


_ACTIVIDAD = {
    "Usos de tótems",
    "¿De dónde vienen?",
    "¿Cuándo se usan los tótems? Día y hora",
    "Lo más consultado en tótems y chatbot",
    "Satisfacción ciudadana",
    "Incidencias críticas",
}
_SOCIAL = {"Menciones en redes", "Lo que se dice del destino"}


def etiquetar(panel: PanelDireccion, est: EstadoDatos) -> PanelDireccion:
    """Corrige el origen de cada dato según qué fuentes son reales y cuáles de demostración."""
    modulo = panel.modulo
    if modulo in FUENTE_VERTICAL and est.demo(modulo):
        _marcar_vertical_demo(panel, modulo)
    demo_ctx = est.fuentes_contexto_demo()
    if demo_ctx:
        for nombre, fuentes in _CONTEXTO.items():
            if origen := _origen_contexto(fuentes, demo_ctx):
                _cambiar(panel, {nombre}, origen)
        for nombre, fuentes in _FUENTES_CONTEXTO.items():
            if origen := _origen_contexto(fuentes, demo_ctx):
                _cambiar_fuentes(panel, {nombre}, origen)
    if est.social_demo:
        _cambiar(panel, _SOCIAL, "demo")
        _cambiar_fuentes(panel, {"Meta (Facebook, Instagram) y X"}, "demo")
    if est.actividad_mixta:
        _cambiar(panel, _ACTIVIDAD, "mixto")
        _cambiar_fuentes(panel, {"Tótems y chatbot"}, "mixto")

    demos = est.verticales_demo()
    if modulo == "resumen":
        for b in panel.bloques:
            if b.tipo == "servicios":
                for t in b.items:
                    t["demo"] = (
                        est.contexto_demo or est.social_demo
                        if t["id"] == "turismo"
                        else est.demo(str(t["id"]))
                    )
            elif (b.tipo == "mapa" and demos) or (
                b.titulo == "¿En qué se va el gasto eléctrico?" and est.demo("energia")
            ):
                b.origen = "demo"
            elif b.tipo == "vivo":
                for it in b.items:
                    vert = "movilidad" if it.get("medidor") == "parkings" else "residuos"
                    it["demo"] = est.demo(vert)
        # El ahorro y el CO₂ se calculan sobre alumbrado y energía.
        if est.demo("alumbrado") or est.demo("energia"):
            _cambiar(panel, {"Ahorro estimado del mes", "CO₂ evitado"}, "demo")
        if demos:
            nombres = ", ".join(_NOMBRE_VERTICAL[v].lower() for v in demos)
            panel.aviso = (
                f"Parte de esta pantalla son datos de demostración: {nombres} aún no están "
                "integrados con los sistemas municipales. Cada dato lleva su etiqueta de origen."
            )
    if modulo == "recomendaciones" and demos:
        panel.aviso = (
            "Las recomendaciones de "
            + ", ".join(_NOMBRE_VERTICAL[v].lower() for v in demos)
            + " se calculan sobre datos de demostración hasta su integración."
        )
    return panel


async def panel(db: AsyncSession, modulo: str) -> PanelDireccion:
    """Panel del módulo indicado (excepto ``recomendaciones``, que necesita la lista)."""
    constructores = {
        "resumen": panel_resumen,
        "turismo": panel_turismo,
        "alumbrado": panel_alumbrado,
        "agua": panel_agua,
        "residuos": panel_residuos,
        "movilidad": panel_movilidad,
        "seguridad": panel_seguridad,
        "energia": panel_energia,
    }
    return etiquetar(await constructores[modulo](db), await estado_datos(db))


__all__ = ["MODULOS", "estado_datos", "etiquetar", "panel", "panel_recomendaciones"]
