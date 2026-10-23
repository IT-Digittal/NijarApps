"""Captura mensual del histórico real y su tratamiento en los paneles de Dirección."""

from __future__ import annotations

from datetime import date

from nijar_dti.services import direccion_panel_service as dp
from nijar_dti.services import metricas_historicas_service as mh


class TestPeriodos:
    def test_periodo_anterior(self):
        assert mh.periodo_anterior(date(2026, 10, 23)) == "2026-09"
        assert mh.periodo_anterior(date(2026, 1, 3)) == "2025-12"

    def test_periodos_entre(self):
        assert mh.periodos_entre("2025-11", "2026-02") == [
            "2025-11",
            "2025-12",
            "2026-01",
            "2026-02",
        ]
        assert mh.periodos_entre("2026-03", "2026-02") == []

    def test_rango_mes_en_hora_de_madrid(self):
        inicio, fin, dias = mh.rango_mes("2026-10")
        assert dias == 31
        # 1 de octubre a las 00:00 en Madrid (CEST, UTC+2) son las 22:00 UTC del 30 de septiembre
        assert inicio.utcoffset().total_seconds() == 7200
        assert (fin - inicio).days == 31

    def test_mes_completo_con_margen_de_datadis(self):
        assert mh.mes_completo(30, 30)
        assert mh.mes_completo(28, 30)
        assert not mh.mes_completo(27, 30)

    def test_origen_real(self):
        assert mh.es_real("datadis")
        assert not mh.es_real("ejemplo")
        assert not mh.es_real(None)

    def test_registro_de_capturadores(self):
        assert set(mh.CAPTURADORES) == {"energia", "alumbrado"}


def _serie(origenes: list[str]) -> dp.SerieHist:
    puntos = [(f"{2024 + i // 12:04d}-{i % 12 + 1:02d}", 100.0 + i) for i in range(len(origenes))]
    return dp.SerieHist(puntos, origenes)


class TestSerieConOrigen:
    def test_origen_del_ultimo_punto(self):
        assert dp.origen_serie(_serie(["ejemplo"] * 24)) == "ejemplo"
        assert dp.origen_serie(_serie(["ejemplo"] * 22 + ["datadis"] * 2)) == "real"
        assert dp.origen_serie(_serie(["ejemplo"] * 22 + ["estimado"] * 2)) == "estimado"
        assert dp.origen_serie(_serie(["datadis"] * 3), "estimado") == "estimado"
        assert dp.origen_serie([("2026-01", 1.0)]) == "real"  # lista sin origen

    def test_nota_al_pie(self):
        assert "ejemplo" in dp.nota_serie(_serie(["ejemplo"] * 24))
        nota = dp.nota_serie(_serie(["ejemplo"] * 22 + ["datadis"] * 2))
        assert nota.startswith("Dato real desde nov 25")
        assert dp.nota_serie(_serie(["datadis"] * 24)) is None
        assert dp.con_nota("Pie", _serie(["datadis"] * 3)) == "Pie"

    def test_interanual_no_mezcla_ejemplo_y_real(self):
        assert dp._yoy(_serie(["ejemplo"] * 24)) is not None
        assert dp._yoy(_serie(["ejemplo"] * 22 + ["datadis"] * 2)) is None
        assert dp._yoy(_serie(["datadis"] * 24)) is not None

    def test_prevision_solo_con_tramo_homogeneo(self):
        mixta = _serie(["ejemplo"] * 22 + ["datadis"] * 2)
        assert dp.cola_homogenea(mixta) == [122.0, 123.0]
        assert dp.prever_mensual(dp.cola_homogenea(mixta)) == []
        assert len(dp.cola_homogenea(_serie(["ejemplo"] * 24))) == 24
        etq, series = dp.serie_con_prevision(mixta, 24, 3)
        assert [s.rol for s in series] == ["dato"]  # sin previsión inventada
        assert len(etq) == 24
