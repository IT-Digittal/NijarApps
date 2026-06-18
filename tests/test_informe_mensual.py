"""Tests del informe mensual (agregación ANS pura y renderizado Markdown)."""

from __future__ import annotations

from nijar_dti.services.informe_render import render_informe_markdown
from nijar_dti.workers.informe_mensual_render import construir_informe_ejemplo


class TestInformeEjemplo:
    def test_construye_report_y_ans(self):
        report, ans = construir_informe_ejemplo()
        # incidencias del seed de demo: 1 crítica, 3 altas (incl. evento seg.)
        assert report.incidencias_criticas == 1
        assert report.incidencias_altas == 3
        assert report.acciones_preventivas_ejecutadas == 2
        assert report.eventos_seguridad == 1
        # disponibilidad por componente presente y acotada
        assert set(report.disponibilidad_por_componente) >= {"plataforma", "totem_1", "chatbot"}
        assert all(0 <= v <= 100 for v in report.disponibilidad_por_componente.values())
        assert ans.incidencias_totales == 6  # reactivas (sin las 2 preventivas)

    def test_render_incluye_secciones(self):
        report, ans = construir_informe_ejemplo()
        md = render_informe_markdown(report, ans)
        assert "Informe mensual de servicio" in md
        assert "Disponibilidad por componente" in md
        assert "Cumplimiento de la matriz ANS" in md
        assert "Estado de seguridad" in md
        assert "KPIs operativos" in md

    def test_render_sin_ans_no_falla(self):
        report, _ = construir_informe_ejemplo()
        md = render_informe_markdown(report, None)
        assert "Cumplimiento de la matriz ANS" not in md
        assert "Disponibilidad por componente" in md


class TestAgregarANS:
    def test_alta_con_un_incumplimiento(self):
        report, ans = construir_informe_ejemplo()
        alta = next(s for s in ans.por_severidad if s.severidad == "alta")
        # 3 altas, una incumple resolución -> 2/3 ≈ 66.7%
        assert alta.total == 3
        assert alta.cumplen_resolucion == 2
        assert alta.porcentaje_cumplimiento == 66.7
