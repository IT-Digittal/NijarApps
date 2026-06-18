"""Tests de los conectores de contexto histórico y del factor de expansión."""

from __future__ import annotations

import pytest

from nijar_dti.connectors.contexto.base import ContextoConnectorError, ContextoRecord
from nijar_dti.connectors.contexto.expansion import (
    FACTOR_EXPANSION_PRELIMINAR,
    calcular_factor_expansion,
)
from nijar_dti.connectors.contexto.fuentes import (
    INEEohConnector,
    INEFronturConnector,
    todos_los_conectores,
)
from nijar_dti.workers.contexto_backfill import generar_dataset


class TestConectoresDryRun:
    def test_todos_devuelven_registros(self):
        for c in todos_los_conectores(dry_run=True):
            registros = c.fetch_series(anios=2)
            assert registros, f"{c.fuente} no devolvió registros"
            assert all(isinstance(r, ContextoRecord) for r in registros)
            assert all(r.fuente == c.fuente for r in registros)

    def test_periodos_unicos_por_clave(self):
        c = INEFronturConnector(dry_run=True)
        registros = c.fetch_series(anios=3)
        claves = [r.clave() for r in registros]
        assert len(claves) == len(set(claves))

    def test_eoh_es_provincia_almeria(self):
        registros = INEEohConnector(dry_run=True).fetch_series(anios=1)
        assert all(r.ambito == "provincia_almeria" for r in registros)
        assert all(r.indicador == "pernoctaciones" for r in registros)

    def test_estacionalidad_verano_mayor_que_invierno(self):
        registros = INEFronturConnector(dry_run=True).fetch_series(anios=1)
        por_periodo = {r.periodo: r.valor for r in registros}
        julios = [v for p, v in por_periodo.items() if p.endswith("-07")]
        eneros = [v for p, v in por_periodo.items() if p.endswith("-01")]
        assert julios and eneros
        assert max(julios) > max(eneros)

    def test_modo_real_no_configurado_falla(self):
        with pytest.raises(ContextoConnectorError):
            INEFronturConnector(dry_run=False).fetch_series()


class TestFactorExpansion:
    def test_preliminar_sin_datos(self):
        fe = calcular_factor_expansion()
        assert fe.factor == FACTOR_EXPANSION_PRELIMINAR
        assert fe.es_preliminar is True

    def test_calibrado_con_eoh(self):
        # 420000 pernoctaciones / 3.5 = 120000 visitantes; muestra 20000 -> factor 6.0
        fe = calcular_factor_expansion(
            muestra_periodo=20_000, pernoctaciones_periodo=420_000, estancia_media_noches=3.5
        )
        assert fe.es_preliminar is False
        assert fe.metodo == "calibrado_eoh"
        assert abs(fe.factor - 6.0) < 0.01
        assert abs(fe.cobertura_estimada_pct - (100 / 6.0)) < 0.1

    def test_muestra_cero_devuelve_preliminar(self):
        fe = calcular_factor_expansion(muestra_periodo=0, pernoctaciones_periodo=100)
        assert fe.es_preliminar is True


class TestWorkerDataset:
    def test_genera_dataset_completo(self):
        ds = generar_dataset(dry_run=True, anios=2)
        assert "registros" in ds
        assert len(ds["registros"]) > 0
        fuentes = {r["fuente"] for r in ds["registros"]}
        assert fuentes == {"ine_frontur", "ine_egatur", "ine_eoh", "junta_andalucia", "aena"}

    def test_registros_serializables(self):
        ds = generar_dataset(dry_run=True, anios=1)
        for r in ds["registros"]:
            assert {"fuente", "indicador", "periodo", "valor"} <= set(r)
