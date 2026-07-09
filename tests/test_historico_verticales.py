"""Tests del seeder histórico de verticales y su comparativa interanual.

Unitarios sin BBDD: validan la generación determinista de la serie y que la
variación interanual coincide con la tendencia configurada.
"""

from __future__ import annotations

from nijar_dti.data.seeds.historico_verticales import (
    INDICADORES,
    generar_historico_seed,
)


def _serie(filas, vertical, indicador):
    pts = [f for f in filas if f["vertical"] == vertical and f["indicador"] == indicador]
    return sorted(pts, key=lambda f: f["periodo"])


class TestSeederHistorico:
    def test_genera_24_meses_por_indicador(self):
        filas = generar_historico_seed(anios=2)
        # 8 indicadores × 24 meses
        assert len(filas) == len(INDICADORES) * 24
        for v, i, *_ in INDICADORES:
            assert len(_serie(filas, v, i)) == 24

    def test_periodos_unicos_y_ordenables(self):
        filas = generar_historico_seed(anios=2)
        s = _serie(filas, "energia", "coste_eur")
        periodos = [f["periodo"] for f in s]
        assert periodos == sorted(periodos)
        assert len(set(periodos)) == 24

    def test_variacion_interanual_igual_a_tendencia(self):
        """La estacionalidad se cancela mes a mes → YoY ≈ tendencia configurada."""
        filas = generar_historico_seed(anios=2)
        for v, i, _nom, unidad, _base, _est, trend, _sent in INDICADORES:
            s = _serie(filas, v, i)
            actual, anterior = s[-1], s[-13]  # mismo mes, un año antes
            var = (actual["valor"] - anterior["valor"]) / anterior["valor"]
            # Indicadores continuos: coincide con la tendencia. Los enteros
            # (unidad "nº", magnitud baja) tienen más error de redondeo.
            tol = 0.03 if unidad == "nº" else 0.005
            assert abs(var - trend) < tol, f"{v}:{i} var={var:.3f} trend={trend}"

    def test_determinista(self):
        assert generar_historico_seed(2) == generar_historico_seed(2)

    def test_sentido_valido(self):
        for *_rest, sentido in [(x[-1],) for x in INDICADORES]:
            assert sentido in {"subir_bueno", "bajar_bueno", "neutro"}
