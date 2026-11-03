"""Energía municipal con datos reales de Datadis: análisis por suministro (sin BD)."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from nijar_dti.services import energia_municipal_service as em


def _sum(cups, tipo="dependencia", potencia=30.0, tarifa="3.0TD"):
    return SimpleNamespace(
        cups=cups,
        edificio="Edificio " + cups,
        tipo=tipo,
        potencia_contratada_kw=potencia,
        metadatos={
            "fuente": "datadis",
            "direccion": "CL " + cups,
            "contrato": {"tarifa_acceso": tarifa, "potencias_kw": [potencia, potencia]},
        },
    )


def _datos(base=1000.0, meses=14, pico=10.0, desde="2025-09", ultima_dias=1, auto=0.0):
    d = em.DatosCups()
    p = desde
    for i in range(meses):
        d.meses[p] = base * (1 + 0.1 * (i == meses - 1))
        d.dias_mes[p] = em.dias_del_mes(p)
        d.autoconsumo[p] = auto
        d.excedente[p] = 0.0
        p = em.mes_anterior(p, -1)
    d.pico_kw = pico
    d.pico_momento = datetime(2026, 7, 1, 12, tzinfo=UTC)
    d.ultima = datetime.now(UTC) - timedelta(days=ultima_dias)
    return d


class TestUtilidades:
    def test_meses(self):
        assert em.mes_anterior("2026-01") == "2025-12"
        assert em.mes_anterior("2026-01", 12) == "2025-01"
        assert em.mes_anterior("2025-12", -1) == "2026-01"
        assert em.ultimo_mes_cerrado(date(2026, 11, 3)) == "2026-10"
        assert em.dias_del_mes("2028-02") == 29

    def test_formato_y_plural(self):
        assert em.miles(3495) == "3.495"
        assert em.suministros(1) == "1 suministro" and em.suministros(3) == "3 suministros"

    def test_potencia_recomendada_con_margen(self):
        assert em.potencia_recomendada(10.0) == 13.0
        assert em.potencia_recomendada(10.1) == 13.5
        assert em.potencia_recomendada(0.2) == 1.0


class TestAnalisisPotencia:
    def test_sobredimensionada(self):
        uso, rec, ahorro = em.analisis_potencia(30.0, 10.0, 12, 30.0)
        assert uso == pytest.approx(33.3) and rec == 13.0 and ahorro == 510.0

    def test_acorde_no_recomienda(self):
        assert em.analisis_potencia(20.0, 15.0, 12, 30.0)[1:] == (None, None)

    def test_poca_historia_no_recomienda(self):
        assert em.analisis_potencia(30.0, 5.0, 3, 30.0)[1:] == (None, None)

    def test_sin_potencia(self):
        assert em.analisis_potencia(None, 5.0, 12, 30.0) == (None, None, None)


def _analisis():
    sums = [
        _sum("ES1", potencia=30.0),
        _sum("ES2", tipo="alumbrado", potencia=10.0, tarifa="2.0TD"),
        _sum("ES3", potencia=5.0, tarifa="2.0TD"),
    ]
    datos = {
        "ES1": _datos(base=4000, pico=8.0, auto=50.0),
        "ES2": _datos(base=2000, pico=8.5),
        "ES3": _datos(base=300, pico=3.0, ultima_dias=30),
    }
    periodo = "2026-10"
    ahora = datetime.now(UTC)
    filas = [em.fila_suministro(s, datos.get(s.cups), periodo, ahora) for s in sums]  # type: ignore[arg-type]
    return em.Analisis(date(2026, 11, 3), periodo, sums, datos, filas, time.monotonic())  # type: ignore[arg-type]


class TestFilasYResumen:
    def test_fila(self):
        a = _analisis()
        f = next(x for x in a.filas if x.cups == "ES1")
        assert f.consumo_mes_kwh == 4400.0 and f.consumo_mes_anterior_kwh == 4000.0
        assert f.variacion_mes_pct == 10.0
        assert f.tarifa == "3.0TD" and f.potencia_contratada_kw == 30.0
        assert f.potencia_recomendada_kw == 10.5 and f.ahorro_potencia_eur_anio == 585.0
        assert f.autoconsumo_12m_kwh == 600.0 and f.estado == "ok"
        assert next(x for x in a.filas if x.cups == "ES3").estado == "sin_datos_recientes"

    def test_resumen(self):
        r = em.resumen(_analisis())
        assert r.hay_datos and r.periodo == "2026-10" and r.suministros_total == 3
        assert r.consumo_mes_kwh == pytest.approx(4400 + 2200 + 330)
        assert r.consumo_mes_alumbrado_kwh == pytest.approx(2200)
        assert r.contratos_a_revisar == 1 and r.cups_con_autoconsumo == 1
        assert r.por_tarifa == {"2.0TD": 2, "3.0TD": 1}
        titulos = [x.titulo for x in r.recomendaciones]
        assert "Ajustar la potencia contratada de 1 suministro" in titulos
        assert any("sin lecturas recientes" in t for t in titulos)
        # mes en curso marcado como incompleto o ausente; los cerrados, completos
        assert all(m.completo for m in r.serie_mensual if m.periodo <= "2026-10")

    def test_sin_datos(self):
        a = _analisis()
        a.datos.clear()
        a.filas = [em.fila_suministro(s, None, a.periodo, datetime.now(UTC)) for s in a.sums]  # type: ignore[arg-type]
        assert em.resumen(a).hay_datos is False

    def test_filtrar_y_ordenar(self):
        filas = _analisis().filas
        assert [f.cups for f in em.filtrar(filas, "alumbrado")] == ["ES2"]
        assert [f.cups for f in em.filtrar(filas, "revisar")] == ["ES1"]
        assert [f.cups for f in em.filtrar(filas, "sin_datos")] == ["ES3"]
        assert [f.cups for f in em.filtrar(filas, buscar="cl es2")] == ["ES2"]
        assert em.filtrar(filas)[0].cups == "ES1"

    def test_csv(self):
        txt = em.csv_suministros(_analisis().filas, "2026-10")
        assert txt.startswith("﻿") and "Consumo 2026-10 (kWh)" in txt
        assert "ES1;CL ES1;edificio;3.0TD;30,00;4400,0" in txt


class TestRutas:
    @pytest.mark.parametrize(
        "ruta",
        [
            "/api/v1/verticales/energia/municipal/resumen",
            "/api/v1/verticales/energia/municipal/suministros",
            "/api/v1/verticales/energia/municipal/suministros.csv",
            "/api/v1/verticales/energia/municipal/suministros/ES1",
        ],
    )
    def test_requieren_auth(self, client, ruta):
        assert client.get(ruta).status_code == 401
