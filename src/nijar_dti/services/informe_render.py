"""Renderizado del informe mensual de servicio (C.1) a Markdown.

Convierte un ``MonthlyReport`` y, opcionalmente, su cumplimiento ANS en un
documento legible para el responsable municipal y como evidencia ante el
PRTR. Función pura (sin BBDD), testeable.
"""

from __future__ import annotations

from nijar_dti.core.ans import SLA_DISPONIBILIDAD_PORC
from nijar_dti.schemas.dashboards import MonthlyReport
from nijar_dti.schemas.incidencias import InformeANS

_MESES = [
    "",
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
]


def _ov(valor, sufijo: str = "") -> str:
    """Formatea un valor opcional ('—' si es None)."""
    return f"{valor}{sufijo}" if valor is not None else "—"


def render_informe_markdown(report: MonthlyReport, ans: InformeANS | None = None) -> str:
    nombre_mes = _MESES[report.month] if 1 <= report.month <= 12 else str(report.month)
    lineas: list[str] = []
    a = lineas.append

    a(f"# Informe mensual de servicio — {nombre_mes.capitalize()} {report.year}")
    a("")
    a("| | |")
    a("|---|---|")
    a("| **Expediente** | 18962/2025 |")
    a("| **Actuación** | C.1 — Mantenimiento y hosting |")
    a(f"| **Periodo** | {nombre_mes} de {report.year} |")
    a("| **Marco** | PRTR · NextGenerationEU · Componente 14 |")
    a("")

    # --- Disponibilidad ---
    a("## 1. Disponibilidad por componente")
    a("")
    a(f"SLA contractual: **{SLA_DISPONIBILIDAD_PORC:.0f}%** mensual.")
    a("")
    a("| Componente | Disponibilidad | Cumple SLA |")
    a("|------------|----------------|------------|")
    for comp, pct in report.disponibilidad_por_componente.items():
        cumple = "✅" if pct >= SLA_DISPONIBILIDAD_PORC else "❌"
        a(f"| {comp} | {pct:.3f}% | {cumple} |")
    if report.disponibilidad_por_componente:
        media = sum(report.disponibilidad_por_componente.values()) / len(
            report.disponibilidad_por_componente
        )
        cumple_media = "✅" if media >= SLA_DISPONIBILIDAD_PORC else "❌"
        a(f"| **Media** | **{media:.3f}%** | {cumple_media} |")
    a("")

    # --- Incidencias ---
    a("## 2. Incidencias")
    a("")
    a("| Métrica | Valor |")
    a("|---------|-------|")
    a(f"| Incidencias críticas | {report.incidencias_criticas} |")
    a(f"| Incidencias altas | {report.incidencias_altas} |")
    a(f"| Incidencias resueltas | {report.incidencias_resueltas} |")
    a(f"| Acciones preventivas ejecutadas | {report.acciones_preventivas_ejecutadas} |")
    a("")

    # --- Cumplimiento ANS ---
    if ans is not None:
        a("## 3. Cumplimiento de la matriz ANS")
        a("")
        a("| Severidad | Total | Cumplen | % cumpl. | T. resp. medio (h) | T. resol. medio (h) |")
        a("|-----------|-------|---------|----------|--------------------|---------------------|")
        for s in ans.por_severidad:
            pct = _ov(s.porcentaje_cumplimiento, "%")  # type: ignore[assignment]
            tr = _ov(s.tiempo_medio_respuesta_h)
            tre = _ov(s.tiempo_medio_resolucion_h)
            a(f"| {s.severidad} | {s.total} | {s.cumplen_resolucion} | {pct} | {tr} | {tre} |")
        a("")

    # --- Seguridad ---
    a("## 4. Estado de seguridad")
    a("")
    a(f"- Eventos de seguridad registrados: **{report.eventos_seguridad}**")
    a(f"- Incidentes confirmados: **{report.incidentes_confirmados}**")
    a("")

    # --- KPIs de uso ---
    a("## 5. KPIs operativos y de uso")
    a("")
    a("| KPI | Valor |")
    a("|-----|-------|")
    a(f"| Interacciones en tótems | {report.interacciones_totems} |")
    a(f"| Sesiones de chatbot | {report.sesiones_chatbot} |")
    a(f"| Visitas web estimadas | {report.visitas_web_estimadas} |")
    a(f"| Menciones del periodo (RRSS) | {report.menciones_periodo} |")
    if report.sentimiento_medio is not None:
        a(f"| Sentimiento medio | {report.sentimiento_medio:.3f} |")
    a("")

    # --- Eficacia digital (GA4) ---
    if report.eficacia_digital:
        ed = report.eficacia_digital
        a("## 6. Eficacia digital (GA4)")
        a("")
        a("| Métrica | Valor |")
        a("|---------|-------|")
        for clave in ("sesiones_30d", "usuarios_30d", "usuarios_nuevos_30d", "paginas_vistas_30d"):
            if clave in ed:
                a(f"| {clave.replace('_', ' ')} | {ed[clave]} |")
        a("")

    a("---")
    a("")
    a(
        "_Informe generado por la Plataforma DTI Níjar a partir del ticketing y "
        "las métricas de la plataforma. Datos verificables y auditables._"
    )
    a("")
    return "\n".join(lineas)
