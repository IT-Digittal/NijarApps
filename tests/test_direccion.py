"""Tests del Cuadro de Mando de Dirección (semáforo, recomendaciones, rutas).

Unitarios sin BBDD: la lógica de semáforo y del motor de reglas es pura; las
rutas se comprueban montadas y protegidas. El 200/403 con datos reales se cubre
en el e2e.
"""

from __future__ import annotations

from types import SimpleNamespace

from nijar_dti.services import direccion_service as ds
from nijar_dti.services import recomendaciones_service as rs


class TestSemaforo:
    def test_agua_ambar_con_fugas(self):
        o = SimpleNamespace(fugas_detectadas=3, sectores_en_alerta=3, rendimiento_medio_pct=88.0)
        assert ds._semaforo_agua(o).estado == "ambar"

    def test_agua_rojo_muchos_sectores(self):
        o = SimpleNamespace(fugas_detectadas=6, sectores_en_alerta=6, rendimiento_medio_pct=70.0)
        assert ds._semaforo_agua(o).estado == "rojo"

    def test_agua_verde_sin_problemas(self):
        o = SimpleNamespace(fugas_detectadas=0, sectores_en_alerta=0, rendimiento_medio_pct=95.0)
        assert ds._semaforo_agua(o).estado == "verde"

    def test_alumbrado_ambar_por_incidencias(self):
        o = SimpleNamespace(en_averia=5, disponibilidad_pct=98.0, sin_comunicacion=1,
                            cuadros_alerta=0, incidencias_abiertas=2)
        assert ds._semaforo_alumbrado(o).estado == "ambar"

    def test_energia_verde_con_autoconsumo(self):
        o = SimpleNamespace(consumo_mes_kwh=1000.0, autoconsumo_pct=12.0)
        assert ds._semaforo_energia(o).estado == "verde"


def _k(**over):
    """Contexto sintético de KPIs para el motor de reglas."""
    base = {
        "alumbrado": SimpleNamespace(sin_comunicacion=0, cuadros_alerta=0, incidencias_abiertas=0),
        "agua": SimpleNamespace(fugas_detectadas=0),
        "residuos": SimpleNamespace(llenado_alto=0),
        "energia": SimpleNamespace(autoconsumo_pct=20.0),
        "big_data": SimpleNamespace(sentimiento_medio=0.5),
        "incidencias": {"criticas": 0},
    }
    base.update(over)
    return base


class TestRecomendaciones:
    def test_todo_ok_devuelve_informativa(self):
        recs = rs._reglas(_k())
        assert len(recs) == 1
        assert recs[0].prioridad == "informativa"

    def test_incidencia_critica_es_prioridad_maxima(self):
        recs = rs._reglas(_k(incidencias={"criticas": 2}))
        assert recs[0].prioridad == "critica"
        assert all(r.motor == "reglas" for r in recs)

    def test_fugas_generan_recomendacion_de_agua(self):
        recs = rs._reglas(_k(agua=SimpleNamespace(fugas_detectadas=3)))
        assert any(r.area == "Ciclo del agua" for r in recs)


class TestClaveEstable:
    def test_clave_determinista(self):
        c1 = rs._clave("Alumbrado público", "Priorizar renovación LED")
        c2 = rs._clave("Alumbrado público", "Priorizar renovación LED")
        assert c1 == c2
        assert " " not in c1 and c1 == c1.lower()

    def test_clave_sin_acentos_ni_simbolos(self):
        assert rs._clave("Energía municipal", "Ampliar autoconsumo") == "energia-municipal--ampliar-autoconsumo"

    def test_reglas_llevan_clave_tras_con_clave(self):
        recs = rs._con_clave(rs._reglas(_k(incidencias={"criticas": 1})))
        assert all(r.clave for r in recs)
        assert recs[0].clave == rs._clave(recs[0].area, recs[0].titulo)


class TestRutasDireccion:
    def test_rutas_montadas(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/direccion/resumen" in paths
        assert "/api/v1/direccion/recomendaciones" in paths
        assert "/api/v1/direccion/recomendaciones/{clave}" in paths

    def test_resumen_requiere_auth(self, client):
        assert client.get("/api/v1/direccion/resumen").status_code == 401

    def test_recomendaciones_requiere_auth(self, client):
        assert client.get("/api/v1/direccion/recomendaciones").status_code == 401

    def test_patch_recomendacion_requiere_auth(self, client):
        assert client.patch("/api/v1/direccion/recomendaciones/x", json={"estado": "aceptada"}).status_code == 401
