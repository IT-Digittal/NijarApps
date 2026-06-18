"""Tests de los modelos predictivos de afluencia (lógica pura)."""

from __future__ import annotations

from datetime import date, timedelta

from nijar_dti.connectors.analytics.forecasting import (
    PuntoSerie,
    ajustar_modelo_estacional,
    detectar_anomalias,
    mape,
    prever_serie,
    rellenar_dias,
    validar_holdout,
)


def _serie_estacional(dias: int, base: float = 100.0) -> list[PuntoSerie]:
    """Serie sintética con pico estival (verano > invierno) y patrón semanal."""
    estacional = [0.4, 0.5, 0.7, 0.9, 1.2, 1.6, 2.0, 2.0, 1.4, 0.9, 0.5, 0.4]
    inicio = date(2024, 1, 1)
    serie = []
    for i in range(dias):
        d = inicio + timedelta(days=i)
        factor_finde = 1.4 if d.weekday() >= 5 else 1.0
        serie.append(PuntoSerie(fecha=d, valor=base * estacional[d.month - 1] * factor_finde))
    return serie


class TestModeloEstacional:
    def test_ajuste_capta_estacionalidad(self):
        modelo = ajustar_modelo_estacional(_serie_estacional(400))
        # julio (pico) debe tener índice mayor que enero (valle)
        assert modelo.indice_mes[7] > modelo.indice_mes[1]
        # fin de semana mayor que entre semana
        assert modelo.indice_dow[5] > modelo.indice_dow[0]

    def test_prediccion_no_negativa(self):
        modelo = ajustar_modelo_estacional(_serie_estacional(120))
        prevision = prever_serie(modelo, date(2025, 7, 1), 10)
        assert len(prevision) == 10
        assert all(p.valor >= 0 for p in prevision)

    def test_serie_vacia(self):
        modelo = ajustar_modelo_estacional([])
        assert modelo.nivel == 0.0
        assert modelo.predecir(date(2025, 1, 1)) == 0.0


class TestMAPE:
    def test_prediccion_perfecta(self):
        assert mape([10, 20, 30], [10, 20, 30]) == 0.0

    def test_ignora_ceros_reales(self):
        # el punto con real=0 se ignora; el resto es perfecto
        assert mape([0, 50], [5, 50]) == 0.0

    def test_sin_puntos_evaluables(self):
        assert mape([0, 0], [3, 4]) is None

    def test_error_porcentual(self):
        # real 100, pred 80 -> 20% de error
        assert mape([100], [80]) == 20.0


class TestValidacionHoldout:
    def test_modelo_estacional_bajo_umbral(self):
        # serie regular y determinista -> el modelo debe predecir bien
        resultado = validar_holdout(_serie_estacional(400), dias_test=14)
        assert resultado.mape is not None
        assert resultado.cumple_umbral is True
        assert resultado.n_test == 14

    def test_serie_insuficiente(self):
        resultado = validar_holdout(_serie_estacional(10), dias_test=14)
        assert resultado.mape is None
        assert resultado.cumple_umbral is False


class TestAnomalias:
    def test_detecta_pico_inyectado(self):
        serie = _serie_estacional(200)
        # inyecta una anomalía clara a mitad de serie
        serie[100] = PuntoSerie(fecha=serie[100].fecha, valor=serie[100].valor * 12)
        anomalias = detectar_anomalias(serie, z=3.0)
        fechas = {a.fecha for a in anomalias}
        assert serie[100].fecha in fechas

    def test_serie_plana_sin_anomalias(self):
        serie = [PuntoSerie(date(2024, 1, 1) + timedelta(days=i), 50.0) for i in range(60)]
        assert detectar_anomalias(serie, z=3.0) == []


class TestRellenarDias:
    def test_rellena_huecos_con_cero(self):
        conteos = {date(2024, 1, 1): 5.0, date(2024, 1, 3): 9.0}
        serie = rellenar_dias(conteos, date(2024, 1, 1), date(2024, 1, 3))
        assert [p.valor for p in serie] == [5.0, 0.0, 9.0]
        assert len(serie) == 3
