"""Descarga de los suministros eléctricos municipales en el formato de los pliegos.

El Servicio de Gestión de Infraestructuras pide los datos de Datadis
estructurados como los anexos de los pliegos de contratación del suministro
eléctrico:

- **Anexo I · Información sobre los puntos de suministro (CUPS)**: una fila por
  CUPS con dirección, municipio, provincia, peaje de acceso (Circular 3/2020),
  tensión, esencial (SÍ/NO), potencias contratadas P1…P6 y distribuidora.
- **Anexo II · Información sobre consumos anuales**: por tipo de peaje, número
  de CUPS y energía activa consumida en cada periodo (T1…T6) en el intervalo
  elegido (por defecto, los últimos 12 meses completos).

La energía por periodo se calcula desde la curva horaria de Datadis aplicando
los periodos horarios de la Circular 3/2020 de la CNMC para la Península. Lo que
Datadis no proporciona (si un suministro es esencial y el CIF de algunas
distribuidoras) queda en blanco para que lo complete el Ayuntamiento.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia
from nijar_dti.models.verticales import SuministroEnergia

MADRID = ZoneInfo("Europe/Madrid")
PERIODOS = ("P1", "P2", "P3", "P4", "P5", "P6")

# Festivos nacionales de fecha fija y no sustituibles (Circular 3/2020): todo el
# día en el periodo más barato, como sábados y domingos.
FESTIVOS_FIJOS = {(1, 1), (1, 5), (15, 8), (12, 10), (1, 11), (6, 12), (8, 12), (25, 12)}

# CIF de las distribuidoras más comunes (por nombre normalizado de Datadis). Las
# que no estén aquí salen en blanco en el anexo para completarlas a mano.
CIF_DISTRIBUIDORAS = {
    "E-DISTRIBUCION": ("B82846817", "E-Distribución Redes Digitales, S.L.U."),
    "EDISTRIBUCION": ("B82846817", "E-Distribución Redes Digitales, S.L.U."),
    "ENDESA": ("B82846817", "E-Distribución Redes Digitales, S.L.U."),
    "I-DE": ("A95075578", "i-DE Redes Eléctricas Inteligentes, S.A.U."),
    "IBERDROLA": ("A95075578", "i-DE Redes Eléctricas Inteligentes, S.A.U."),
}

# Temporadas de los peajes de 6 periodos en la Península.
_TEMPORADA = {
    1: "alta",
    2: "alta",
    7: "alta",
    12: "alta",
    3: "media_alta",
    11: "media_alta",
    6: "media",
    8: "media",
    9: "media",
    4: "baja",
    5: "baja",
    10: "baja",
}
# (periodo de las horas punta, periodo de las horas llano) por temporada
_PUNTA_LLANO = {
    "alta": ("P1", "P2"),
    "media_alta": ("P2", "P3"),
    "media": ("P3", "P4"),
    "baja": ("P4", "P5"),
}


def es_dia_valle(dia: date) -> bool:
    """Sábado, domingo o festivo nacional de fecha fija."""
    return dia.weekday() >= 5 or (dia.day, dia.month) in FESTIVOS_FIJOS


def periodo_tarifario(momento_local: datetime, tarifa: str | None) -> str:
    """Periodo (P1…P6) de la hora que empieza en ``momento_local`` (hora de Madrid).

    - 2.0TD: P1 punta 10-14 y 18-22 h; P2 llano 8-10, 14-18 y 22-24 h; P3 valle
      0-8 h, fines de semana y festivos.
    - 3.0TD y 6.xTD: según la temporada del mes, las horas de 9-14 y 18-22 h son
      el periodo «punta» de la temporada y las de 8-9, 14-18 y 22-24 h el «llano»;
      0-8 h, fines de semana y festivos son P6.
    """
    h = momento_local.hour
    valle = es_dia_valle(momento_local.date())
    if (tarifa or "").upper().startswith("2.0"):
        if valle or h < 8:
            return "P3"
        return "P1" if 10 <= h < 14 or 18 <= h < 22 else "P2"
    if valle or h < 8:
        return "P6"
    punta, llano = _PUNTA_LLANO[_TEMPORADA[momento_local.month]]
    return punta if 9 <= h < 14 or 18 <= h < 22 else llano


def cif_distribuidora(nombre: str | None) -> tuple[str, str]:
    """(CIF, denominación) de la distribuidora; CIF vacío si no se conoce."""
    clave = (nombre or "").upper().replace(" ", "")
    for patron, (cif, razon) in CIF_DISTRIBUIDORAS.items():
        if patron.replace(" ", "") in clave:
            return cif, razon
    return "", (nombre or "").strip()


def ultimos_12_meses(hoy: date) -> tuple[date, date]:
    """Primer día de hace 12 meses y último día del mes pasado."""
    fin = hoy.replace(day=1) - timedelta(days=1)
    inicio = date(fin.year - 1, fin.month, 1) + timedelta(days=32)
    return inicio.replace(day=1), fin


# ------------------------------------------------------------------ datos ----
@dataclass
class FilaAnexoI:
    cups: str
    direccion: str
    municipio: str
    provincia: str
    peaje: str
    tension: str
    esencial: str
    potencias: list[float | None]
    cif_distribuidora: str
    distribuidora: str
    tipo: str


def _meta(s: SuministroEnergia) -> dict[str, Any]:
    return s.metadatos if isinstance(s.metadatos, dict) else {}


async def suministros_reales(db: AsyncSession) -> list[SuministroEnergia]:
    """Suministros cargados desde la API privada de Datadis (no los de demo)."""
    q = (
        select(SuministroEnergia)
        .where(SuministroEnergia.metadatos["fuente"].as_string() == "datadis")
        .order_by(SuministroEnergia.cups)
    )
    return list((await db.execute(q)).scalars().all())


def fila_anexo_i(s: SuministroEnergia) -> FilaAnexoI:
    m = _meta(s)
    contrato = m.get("contrato")
    c: dict[str, Any] = contrato if isinstance(contrato, dict) else {}
    potencias = list(c.get("potencias_kw") or [])[:6]
    potencias += [None] * (6 - len(potencias))
    cif, razon = cif_distribuidora(c.get("distribuidora") or m.get("distribuidora"))
    esencial = m.get("esencial")
    return FilaAnexoI(
        cups=s.cups,
        direccion=str(m.get("direccion") or s.edificio or ""),
        municipio=str(c.get("municipio") or m.get("municipio") or ""),
        provincia=str(c.get("provincia") or m.get("provincia") or ""),
        peaje=str(c.get("tarifa_acceso") or ""),
        tension=str(c.get("tension") or ""),
        esencial="SI" if esencial is True else ("NO" if esencial is False else ""),
        potencias=potencias,
        cif_distribuidora=cif,
        distribuidora=razon,
        tipo=str(s.tipo or ""),
    )


async def energia_por_periodo(
    db: AsyncSession, cups_tarifa: dict[str, str], desde: date, hasta: date
) -> dict[str, dict[str, float]]:
    """kWh por CUPS y periodo tarifario entre ``desde`` y ``hasta`` (incluidos).

    Agrega en la BD por hora local (día, hora) para no traer cada lectura.
    """
    if not cups_tarifa:
        return {}
    inicio = datetime.combine(desde, datetime.min.time(), tzinfo=MADRID)
    fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time(), tzinfo=MADRID)
    # hora local de Madrid (literal en el SQL para que GROUP BY coincida con el SELECT)
    hora_local = func.date_trunc(
        literal_column("'hour'"),
        func.timezone(literal_column("'Europe/Madrid'"), ConsumoHorarioEnergia.momento),
    )
    filas = (
        await db.execute(
            select(
                ConsumoHorarioEnergia.cups,
                hora_local,
                func.sum(ConsumoHorarioEnergia.consumo_kwh),
            )
            .where(
                ConsumoHorarioEnergia.cups.in_(list(cups_tarifa)),
                ConsumoHorarioEnergia.momento >= inicio,
                ConsumoHorarioEnergia.momento < fin,
            )
            .group_by(ConsumoHorarioEnergia.cups, hora_local)
        )
    ).all()
    salida: dict[str, dict[str, float]] = defaultdict(lambda: dict.fromkeys(PERIODOS, 0.0))
    for cups, hora, kwh in filas:
        p = periodo_tarifario(hora, cups_tarifa.get(cups))
        salida[cups][p] += float(kwh or 0)
    return dict(salida)


@dataclass
class FilaAnexoII:
    peaje: str
    num_cups: int
    energia: dict[str, float]


async def anexos(
    db: AsyncSession, desde: date, hasta: date, tipo: str | None = None
) -> tuple[list[FilaAnexoI], list[FilaAnexoII], dict[str, dict[str, float]]]:
    """Filas de los dos anexos (y la energía por CUPS) para el intervalo dado.

    ``tipo``: ``"alumbrado"`` solo alumbrado público, ``"edificios"`` el resto.
    """
    sums = await suministros_reales(db)
    if tipo == "alumbrado":
        sums = [s for s in sums if (s.tipo or "").lower() == "alumbrado"]
    elif tipo == "edificios":
        sums = [s for s in sums if (s.tipo or "").lower() != "alumbrado"]
    filas_i = [fila_anexo_i(s) for s in sums]
    por_cups = await energia_por_periodo(db, {f.cups: f.peaje for f in filas_i}, desde, hasta)
    grupos: dict[str, FilaAnexoII] = {}
    for f in filas_i:
        g = grupos.setdefault(
            f.peaje or "Sin dato",
            FilaAnexoII(f.peaje or "Sin dato", 0, dict.fromkeys(PERIODOS, 0.0)),
        )
        g.num_cups += 1
        for p, v in por_cups.get(f.cups, {}).items():
            g.energia[p] += v
    orden = sorted(grupos.values(), key=lambda g: (g.peaje == "Sin dato", g.peaje))
    return filas_i, orden, por_cups


# --------------------------------------------------------------- ficheros ----
CABECERA_I = [
    "CUPS",
    "Dirección Suministro",
    "Municipio",
    "Provincia",
    "Categoría Peaje de Acceso (Tarifa circular 3/2020)",
    "Tensión de conexión (V)",
    "Esencial (SI/NO)",
    "P1 (kW)",
    "P2 (kW)",
    "P3 (kW)",
    "P4 (kW)",
    "P5 (kW)",
    "P6 (kW)",
    "CIF Distribuidora",
    "Denominación Distribuidora",
    "Tipo (plataforma)",
]
CABECERA_II = ["Número de CUPS por Tarifa", "Tipo Tarifa"] + [f"T{i} (kWh)" for i in range(1, 7)]


def _valores_i(f: FilaAnexoI) -> list[Any]:
    return [
        f.cups,
        f.direccion,
        f.municipio,
        f.provincia,
        f.peaje,
        f.tension,
        f.esencial,
        *f.potencias,
        f.cif_distribuidora,
        f.distribuidora,
        f.tipo,
    ]


def _valores_ii(g: FilaAnexoII) -> list[Any]:
    return [g.num_cups, g.peaje, *(round(g.energia[p], 2) for p in PERIODOS)]


def csv_anexo(anexo: str, filas_i: list[FilaAnexoI], filas_ii: list[FilaAnexoII]) -> str:
    """CSV (separador «;» y coma decimal, como lo abre Excel en español)."""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")

    def fmt(v: Any) -> Any:
        if isinstance(v, float):
            return f"{v:.2f}".replace(".", ",")
        return "" if v is None else v

    if anexo == "i":
        w.writerow(CABECERA_I)
        w.writerows([fmt(v) for v in _valores_i(f)] for f in filas_i)
    else:
        w.writerow(CABECERA_II)
        w.writerows([fmt(v) for v in _valores_ii(g)] for g in filas_ii)
    return "﻿" + buf.getvalue()  # BOM: Excel detecta UTF-8 (tildes y ñ)


def excel_anexos(
    filas_i: list[FilaAnexoI],
    filas_ii: list[FilaAnexoII],
    por_cups: dict[str, dict[str, float]],
    desde: date,
    hasta: date,
) -> bytes:
    """Libro Excel con el Anexo I, el Anexo II y el detalle de energía por CUPS."""
    from openpyxl import Workbook  # type: ignore[import-untyped]
    from openpyxl.styles import Alignment, Font, PatternFill  # type: ignore[import-untyped]
    from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]

    libro = Workbook()
    negrita = Font(bold=True, color="FFFFFF")
    relleno = PatternFill("solid", fgColor="1F3A5F")
    centrado = Alignment(horizontal="center", vertical="center", wrap_text=True)
    periodo_txt = f"{desde:%d/%m/%Y} – {hasta:%d/%m/%Y}"

    def cabecera(hoja: Any, fila: int, grupos: list[tuple[str, int]], columnas: list[str]) -> None:
        col = 1
        for texto, ancho in grupos:
            hoja.cell(row=fila, column=col, value=texto)
            if ancho > 1:
                hoja.merge_cells(
                    start_row=fila, start_column=col, end_row=fila, end_column=col + ancho - 1
                )
            col += ancho
        for i, texto in enumerate(columnas, start=1):
            hoja.cell(row=fila + 1, column=i, value=texto)
        for f in (fila, fila + 1):
            for c in range(1, len(columnas) + 1):
                celda = hoja.cell(row=f, column=c)
                celda.font, celda.fill, celda.alignment = negrita, relleno, centrado
        hoja.row_dimensions[fila + 1].height = 45
        hoja.freeze_panes = hoja.cell(row=fila + 2, column=2)

    # --- Anexo I
    h1 = libro.active
    h1.title = "Anexo I - CUPS"
    h1["A1"] = "ANEXO I: INFORMACIÓN SOBRE LOS PUNTOS DE SUMINISTROS (CUPS)"
    h1["A1"].font = Font(bold=True, size=13)
    h1["A2"] = f"Ayuntamiento de Níjar · fuente Datadis · {len(filas_i)} suministros"
    cabecera(
        h1,
        4,
        [
            ("Identificación", 1),
            ("Localización", 3),
            ("Datos generales", 3),
            ("Potencia contratada (kW)", 6),
            ("Distribuidora", 2),
            ("", 1),
        ],
        CABECERA_I,
    )
    for f in filas_i:
        h1.append(_valores_i(f))
    anchos_i = [24, 40, 14, 12, 16, 14, 10, 9, 9, 9, 9, 9, 9, 13, 34, 14]
    for i, a in enumerate(anchos_i, start=1):
        h1.column_dimensions[get_column_letter(i)].width = a

    # --- Anexo II
    h2 = libro.create_sheet("Anexo II - Consumos")
    h2["A1"] = "ANEXO II: INFORMACIÓN SOBRE CONSUMOS ANUALES"
    h2["A1"].font = Font(bold=True, size=13)
    h2["A2"] = (
        f"Energía activa consumida por periodo tarifario (kWh) · {periodo_txt} · "
        "periodos de la Circular 3/2020 (Península)"
    )
    cabecera(h2, 4, [("Agrupación", 2), ("Energía activa (kWh)", 6)], CABECERA_II)
    for g in filas_ii:
        h2.append(_valores_ii(g))
    h2.append(
        [sum(g.num_cups for g in filas_ii), "TOTAL"]
        + [round(sum(g.energia[p] for g in filas_ii), 2) for p in PERIODOS]
    )
    for c in h2[h2.max_row]:
        c.font = Font(bold=True)
    for i, a in enumerate([16, 14, 14, 14, 14, 14, 14, 14], start=1):
        h2.column_dimensions[get_column_letter(i)].width = a

    # --- Detalle por CUPS
    h3 = libro.create_sheet("Detalle por CUPS")
    h3.append(
        ["CUPS", "Tipo Tarifa", "Tipo (plataforma)"]
        + [f"T{i} (kWh)" for i in range(1, 7)]
        + ["Total (kWh)"]
    )
    for c in h3[1]:
        c.font, c.fill, c.alignment = negrita, relleno, centrado
    for f in filas_i:
        e = por_cups.get(f.cups, dict.fromkeys(PERIODOS, 0.0))
        h3.append(
            [f.cups, f.peaje, f.tipo]
            + [round(e[p], 2) for p in PERIODOS]
            + [round(sum(e.values()), 2)]
        )
    for i, a in enumerate([24, 12, 14] + [13] * 7, start=1):
        h3.column_dimensions[get_column_letter(i)].width = a
    h3.freeze_panes = "B2"

    # --- Notas
    h4 = libro.create_sheet("Notas")
    for linea in (
        "Origen: API privada de Datadis (curva horaria y detalle de contrato de cada CUPS).",
        f"Periodo de consumo: {periodo_txt}.",
        "T1…T6 = energía activa en cada periodo de la Circular 3/2020 de la CNMC (Península):",
        "  2.0TD → P1 punta (10-14 y 18-22 h laborables), P2 llano,",
        "  P3 valle (0-8 h, fines de semana y festivos).",
        "  3.0TD / 6.xTD → 6 periodos según temporada (alta: ene, feb, jul, dic;",
        "  media-alta: mar, nov; media: jun, ago, sep; baja: abr, may, oct).",
        "  Fines de semana y festivos nacionales de fecha fija = P6.",
        "Columnas en blanco: «Esencial» y el CIF de algunas distribuidoras no los da Datadis;",
        "debe completarlos el Ayuntamiento. La tensión es la que informa la distribuidora.",
        "Un CUPS sin consumo en el periodo no tenía lecturas horarias publicadas en Datadis.",
    ):
        h4.append([linea])
    h4.column_dimensions["A"].width = 110

    buf = io.BytesIO()
    libro.save(buf)
    return buf.getvalue()
