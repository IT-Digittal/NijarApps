"""Informe mensual de visibilidad por anunciante (PDF).

Genera el justificante que el Ayuntamiento adjunta a la facturación de cada
campaña: impresiones y toques de la empresa en los tótems, desglosados por
semana del mes, con metodología explicada al pie. Render con fpdf2 (Python
puro, tipografía core latin-1 — suficiente para el castellano).
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any
from uuid import UUID

from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.empresa_anunciante import EmpresaAnunciante, MetricaPublicidad
from nijar_dti.services.publicidad_service import obtener_empresa

AZUL = (14, 58, 120)
NARANJA = (224, 145, 47)
GRIS = (103, 118, 154)


def agregar_semanas(
    filas: list[tuple[date, int, int]], anio: int, mes: int
) -> list[dict[str, Any]]:
    """Agrupa los agregados diarios en semanas del mes (1-7, 8-14, …).

    Devuelve una fila por semana aunque no haya datos (0), para que el informe
    siempre muestre el mes completo.
    """
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    semanas = []
    inicio = 1
    while inicio <= ultimo_dia:
        fin = min(inicio + 6, ultimo_dia)
        imp = sum(i for f, i, _ in filas if inicio <= f.day <= fin)
        toq = sum(t for f, _, t in filas if inicio <= f.day <= fin)
        semanas.append({"etiqueta": f"{inicio}-{fin}", "impresiones": imp, "toques": toq})
        inicio = fin + 1
    return semanas


async def datos_informe(db: AsyncSession, empresa_id: UUID, anio: int, mes: int) -> dict[str, Any]:
    empresa = await obtener_empresa(db, empresa_id)
    desde = date(anio, mes, 1)
    hasta = date(anio, mes, calendar.monthrange(anio, mes)[1])
    filas = [
        (f, int(i or 0), int(t or 0))
        for f, i, t in (
            await db.execute(
                select(
                    MetricaPublicidad.fecha,
                    MetricaPublicidad.impresiones,
                    MetricaPublicidad.toques,
                )
                .where(
                    MetricaPublicidad.empresa_id == empresa_id,
                    MetricaPublicidad.fecha >= desde,
                    MetricaPublicidad.fecha <= hasta,
                )
                .order_by(MetricaPublicidad.fecha)
            )
        ).all()
    ]
    semanas = agregar_semanas(filas, anio, mes)
    return {
        "empresa": empresa,
        "anio": anio,
        "mes": mes,
        "semanas": semanas,
        "total_impresiones": sum(int(s["impresiones"]) for s in semanas),
        "total_toques": sum(int(s["toques"]) for s in semanas),
        "dias_con_datos": len(filas),
    }


MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


SECTOR_ETIQUETAS = {
    "gastronomia": "Gastronomía",
    "alojamiento": "Alojamiento",
    "ocio_activo": "Ocio activo",
    "comercio": "Comercio",
    "servicios": "Servicios",
    "otro": "Otro",
}


def _latin(texto: str) -> str:
    return texto.encode("latin-1", "replace").decode("latin-1")


def render_pdf(datos: dict[str, Any]) -> bytes:
    """Compone el PDF del informe (una página A4)."""
    empresa: EmpresaAnunciante = datos["empresa"]
    anio, mes = int(datos["anio"]), int(datos["mes"])
    semanas: list[dict[str, Any]] = datos["semanas"]
    periodo = f"{MESES[mes - 1].capitalize()} {anio}"

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Cabecera institucional
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 210, 26, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 15)
    pdf.set_xy(12, 7)
    pdf.cell(0, 6, _latin("Ayuntamiento de Níjar · Plataforma DTI"))
    pdf.set_font("helvetica", "", 10)
    pdf.set_xy(12, 14)
    pdf.cell(0, 6, _latin("Informe de visibilidad publicitaria en los tótems del destino"))

    # Datos del anunciante y periodo
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(12, 34)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 8, _latin(empresa.nombre))
    pdf.set_xy(12, 43)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*GRIS)
    detalles = " · ".join(
        x
        for x in [
            SECTOR_ETIQUETAS.get(empresa.sector, empresa.sector.replace("_", " ")),
            empresa.nucleo,
            empresa.direccion,
        ]
        if x
    )
    pdf.cell(0, 5, _latin(detalles))
    pdf.set_xy(12, 50)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(*NARANJA)
    pdf.cell(0, 6, _latin(f"Periodo: {periodo}"))

    # Totales
    pdf.set_xy(12, 62)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    total_imp = int(datos["total_impresiones"])
    total_toq = int(datos["total_toques"])
    pdf.cell(90, 8, _latin(f"Impresiones totales: {total_imp:,}".replace(",", ".")))
    pdf.cell(90, 8, _latin(f"Toques totales: {total_toq:,}".replace(",", ".")))

    # Tabla semanal
    y = 78
    pdf.set_xy(12, y)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(238, 242, 250)
    pdf.cell(60, 8, _latin("Semana (días del mes)"), border=1, fill=True)
    pdf.cell(60, 8, "Impresiones", border=1, fill=True, align="R")
    pdf.cell(60, 8, "Toques", border=1, fill=True, align="R")
    pdf.set_font("helvetica", "", 10)
    for s in semanas:
        pdf.set_xy(12, pdf.get_y() + 8)
        pdf.cell(60, 8, _latin(str(s["etiqueta"])), border=1)
        pdf.cell(60, 8, str(s["impresiones"]), border=1, align="R")
        pdf.cell(60, 8, str(s["toques"]), border=1, align="R")

    # Gráfico de barras semanal (impresiones)
    top = pdf.get_y() + 20
    maximo = max([int(s["impresiones"]) for s in semanas] + [1])
    alto_max, ancho, hueco = 40.0, 26.0, 10.0
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*AZUL)
    pdf.set_xy(12, top - 8)
    pdf.cell(0, 5, _latin("Impresiones por semana"))
    x = 16.0
    base_y = top + alto_max
    for s in semanas:
        h = alto_max * int(s["impresiones"]) / maximo
        pdf.set_fill_color(*AZUL)
        pdf.rect(x, base_y - h, ancho, h, "F")
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*GRIS)
        pdf.set_xy(x, base_y + 2)
        pdf.cell(ancho, 4, _latin(str(s["etiqueta"])), align="C")
        pdf.set_xy(x, base_y - h - 5)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(ancho, 4, str(s["impresiones"]), align="C")
        x += ancho + hueco

    # Metodología y pie
    pdf.set_xy(12, base_y + 16)
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(
        186,
        4.2,
        _latin(
            "Metodología: una impresión se contabiliza cada vez que la ficha del anunciante "
            "se muestra en pantalla en el apartado «Empresas» de los tótems del destino; un "
            "toque, cada vez que un visitante pulsa la ficha. El registro es anónimo y "
            "agregado por día, sin recoger datos personales de los visitantes. Informe "
            "generado automáticamente por la Plataforma DTI (Exp. 18962/2025)."
        ),
    )

    return bytes(pdf.output())
