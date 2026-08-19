"""CLI para generar un informe mensual de servicio (C.1) en Markdown.

Genera un informe de ejemplo a partir de las incidencias de demostración del
mes natural anterior (en memoria, sin BBDD), aplicando las mismas funciones de
agregación que usa la API. Sirve como plantilla cumplimentada para el dossier
Pre-SAT.

Uso:
    python -m nijar_dti.workers.informe_mensual_render --output informe.md
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from types import SimpleNamespace

from nijar_dti.data.seeds.demo_data import _mes_anterior, generar_incidencias_seed
from nijar_dti.schemas.dashboards import MonthlyReport
from nijar_dti.services.incidencias_service import (
    agregar_cumplimiento_ans,
    calcular_disponibilidad,
    resumen_incidencias,
)
from nijar_dti.services.informe_render import render_informe_markdown


def _a_objeto(d: dict) -> SimpleNamespace:
    """Convierte un dict de incidencia de demo en un objeto con sus atributos."""
    return SimpleNamespace(
        severidad=d["severidad"],
        componente=d["componente"],
        detectada_en=d["detectada_en"],
        respondida_en=d.get("respondida_en"),
        resuelta_en=d.get("resuelta_en"),
        afecta_disponibilidad=d.get("afecta_disponibilidad", False),
        es_preventiva=d.get("es_preventiva", False),
        es_evento_seguridad=d.get("es_evento_seguridad", False),
        incidente_confirmado=d.get("incidente_confirmado", False),
    )


def construir_informe_ejemplo() -> tuple[MonthlyReport, object]:
    inicio, fin = _mes_anterior(datetime.now(UTC))
    incidencias = [_a_objeto(d) for d in generar_incidencias_seed()]

    disponibilidad = calcular_disponibilidad(incidencias, inicio, fin)  # type: ignore[arg-type]
    resumen = resumen_incidencias(incidencias)  # type: ignore[arg-type]
    ans = agregar_cumplimiento_ans(incidencias, inicio, fin)

    report = MonthlyReport(
        year=inicio.year,
        month=inicio.month,
        disponibilidad_por_componente=disponibilidad,
        # Valores de tráfico de ejemplo (en producción salen de la BBDD)
        interacciones_totems=1840,
        sesiones_chatbot=512,
        visitas_web_estimadas=8420,
        incidencias_criticas=resumen["criticas"],
        incidencias_altas=resumen["altas"],
        incidencias_resueltas=resumen["resueltas"],
        eventos_seguridad=resumen["eventos_seguridad"],
        incidentes_confirmados=resumen["incidentes_confirmados"],
        acciones_preventivas_ejecutadas=resumen["preventivas"],
        sentimiento_medio=0.412,
        menciones_periodo=327,
        eficacia_digital={
            "configurado": False,
            "sesiones_30d": 8420,
            "usuarios_30d": 6120,
            "usuarios_nuevos_30d": 4840,
            "paginas_vistas_30d": 21350,
        },
    )
    return report, ans


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera el informe mensual C.1 en Markdown")
    parser.add_argument("--output", type=str, default=None, help="Ruta del .md de salida")
    args = parser.parse_args(argv)

    report, ans = construir_informe_ejemplo()
    md = render_informe_markdown(report, ans)  # type: ignore[arg-type]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Informe escrito en {args.output}")
    else:
        print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
