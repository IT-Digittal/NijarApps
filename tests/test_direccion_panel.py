"""Vista de Gobierno 2.0: lógica pura de los paneles por módulo y rutas."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from nijar_dti.schemas.direccion import PanelDireccion, RecomendacionIA
from nijar_dti.services import direccion_panel_service as dp
from nijar_dti.services import recomendaciones_service as rs


def _serie(meses: int, base: float = 100.0, crecimiento: float = 0.0) -> list[tuple[str, float]]:
    """Serie mensual estacional sintética (pico en verano) desde 2024-01."""
    estacion = [0.8, 0.8, 0.9, 1.0, 1.1, 1.3, 1.4, 1.4, 1.2, 1.0, 0.9, 0.8]
    puntos = []
    for i in range(meses):
        y, m = 2024 + i // 12, i % 12 + 1
        puntos.append((f"{y:04d}-{m:02d}", base * estacion[m - 1] * (1 + crecimiento) ** (i / 12)))
    return puntos


class TestFormato:
    def test_fmt_num_espanol(self):
        assert dp.fmt_num(1234567) == "1.234.567"
        assert dp.fmt_num(1234.5, 1) == "1.234,5"
        assert dp.fmt_num(None) == "—"

    def test_delta_pct(self):
        assert dp.delta_pct(110, 100) == 10.0
        assert dp.delta_pct(5, 0) is None
        assert dp.delta_pct(None, 3) is None

    def test_texto_delta_sentido(self):
        assert dp.texto_delta(4.2) == ("+4,2 %", "bueno")
        assert dp.texto_delta(-6.0, bajar_bueno=True) == ("−6,0 %", "bueno")
        assert dp.texto_delta(6.0, bajar_bueno=True)[1] == "malo"
        assert dp.texto_delta(0.2)[1] == "neutro"
        assert dp.texto_delta(None) == (None, "neutro")

    def test_periodos(self):
        assert dp.etiqueta_periodo("2026-03") == "mar 26"
        assert dp.siguiente_periodo("2026-11", 3) == "2027-02"


class TestPrevision:
    def test_sin_historico_suficiente_no_preve(self):
        assert dp.prever_mensual([1.0] * 14) == []

    def test_reproduce_estacionalidad_y_tendencia(self):
        serie = _serie(24, crecimiento=0.10)
        prev = dp.prever_mensual([v for _, v in serie], 3)
        assert len(prev) == 3
        # el mes siguiente a diciembre es enero: ≈ enero del año anterior × 1,10
        enero_previo = serie[12][1]
        assert prev[0][0] == pytest.approx(enero_previo * 1.10, rel=0.02)
        for valor, inf, sup in prev:
            assert inf <= valor <= sup

    def test_serie_con_prevision_alinea_etiquetas(self):
        etq, series = dp.serie_con_prevision(_serie(30), 24, 3)
        assert len(etq) == 27
        assert all(len(s.valores) == 27 for s in series)
        roles = [s.rol for s in series]
        assert roles == ["dato", "prevision", "banda_inf", "banda_sup"]
        # la previsión arranca en el último dato real
        assert series[1].valores[23] == series[0].valores[23]

    def test_comparativa_anual(self):
        etq, series, anio = dp.comparativa_anual(_serie(21))  # hasta sep de 2025
        assert anio == 2025 and etq[0] == "ene" and len(etq) == 12
        actual = next(s for s in series if s.nombre == "2025")
        assert actual.valores[9] is None  # octubre aún no ha llegado
        prevision = next(s for s in series if s.rol == "prevision")
        assert prevision.valores[9] is not None and prevision.valores[8] is not None

    def test_comparativa_anual_sin_enlazar_para_barras(self):
        _, series, _ = dp.comparativa_anual(_serie(21), enlazar=False)
        prevision = next(s for s in series if s.rol == "prevision")
        assert prevision.valores[8] is None


class TestModelosAuxiliares:
    def test_llenado_previsto(self):
        assert dp.llenado_previsto(50, "envases", 24) == pytest.approx(72.0)
        assert dp.llenado_previsto(95, "resto", 48) == 100.0

    def test_nucleo_de(self):
        assert dp.nucleo_de("San José puerto") == dp.nucleo_de("San José playas")
        assert dp.nucleo_de("Níjar casco") is not None
        assert dp.nucleo_de("Sector desconocido") is None

    def test_estado_rendimiento(self):
        assert dp.estado_rendimiento(90) == "verde"
        assert dp.estado_rendimiento(80) == "ambar"
        assert dp.estado_rendimiento(70) == "rojo"

    def test_frase_portada(self):
        assert dp.frase_portada("correcto", 0) == "Níjar funciona hoy con normalidad"
        assert "4 áreas" in dp.frase_portada("atencion", 4)
        assert "1 área " in dp.frase_portada("atencion", 1)
        assert "decisión" in dp.frase_portada("critico", 3)

    def test_resumen_semanal(self):
        r = SimpleNamespace(
            estado_global=84,
            servicios_ok=3,
            servicios_total=7,
            areas_alerta=["Residuos"],
            ahorro_estimado_eur_mes=3427,
            co2_evitado_t_anio=47.4,
            incidencias_criticas=1,
        )
        recs = [
            RecomendacionIA(
                titulo="Reparar cámara",
                area="Seguridad",
                justificacion="x",
                impacto="y",
                prioridad="critica",
                accion="z",
            )
        ]
        txt = dp.resumen_semanal(r, recs)
        assert "84 sobre 100" in txt and "residuos" in txt and "reparar cámara" in txt


class TestReglasNuevas:
    def _k(self, **over):
        base = {
            "alumbrado": SimpleNamespace(
                sin_comunicacion=0, cuadros_alerta=0, incidencias_abiertas=0
            ),
            "agua": SimpleNamespace(fugas_detectadas=0),
            "residuos": SimpleNamespace(llenado_alto=0),
            "energia": SimpleNamespace(autoconsumo_pct=20.0),
            "big_data": SimpleNamespace(sentimiento_medio=0.5),
            "incidencias": {"criticas": 0},
        }
        base.update(over)
        return base

    def test_parking_saturado_genera_recomendacion_de_movilidad(self):
        mov = SimpleNamespace(ocupacion_parking_pct=96.0, plazas_ocupadas=960, plazas_totales=1000)
        recs = rs._reglas(self._k(movilidad=mov))
        r = next(x for x in recs if x.area == "Movilidad")
        assert r.prioridad == "alta"

    def test_camara_caida_genera_recomendacion_de_seguridad(self):
        seg = SimpleNamespace(sin_comunicacion=1, pct_online=96.0)
        recs = rs._reglas(self._k(seguridad=seg))
        assert any(x.area == "Seguridad" for x in recs)

    def test_sin_datos_de_movilidad_ni_seguridad_no_falla(self):
        assert len(rs._reglas(self._k())) == 1


class TestRutasPanel:
    def test_rutas_montadas(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/direccion/panel/{modulo}" in paths
        assert "/api/v1/direccion/panel/recomendaciones" in paths

    @pytest.mark.parametrize("modulo", ["resumen", "turismo", "energia", "recomendaciones"])
    def test_panel_requiere_auth(self, client, modulo):
        assert client.get(f"/api/v1/direccion/panel/{modulo}").status_code == 401

    def test_modulos_cubren_la_vista_de_gobierno(self):
        assert set(dp.MODULOS) == {
            "resumen",
            "turismo",
            "alumbrado",
            "agua",
            "residuos",
            "movilidad",
            "seguridad",
            "energia",
            "recomendaciones",
        }
        assert {"hero", "kpis", "bloques"} <= set(PanelDireccion.model_fields)


class TestEtiquetadoDemo:
    """Los datos de verticales en demo y las series sintéticas no se presentan como reales."""

    def _panel(self, modulo: str):
        from datetime import UTC, datetime

        from nijar_dti.schemas.direccion import BloquePanel, HeroPanel, KpiPanel

        return PanelDireccion(
            modulo=modulo,
            titulo="t",
            intro="i",
            hero=HeroPanel(fondo=modulo, titulo="h", subtitulo="s"),
            kpis=[
                KpiPanel(etiqueta="Cámaras online", valor="96"),
                KpiPanel(etiqueta="Incidencias del mes", valor="48", origen="ejemplo"),
                KpiPanel(etiqueta="Consumo del último mes", valor="10", origen="real"),
                KpiPanel(etiqueta="Pernoctaciones", valor="1"),
                KpiPanel(etiqueta="Usos de tótems", valor="2"),
            ],
            bloques=[
                BloquePanel(tipo="ranking", titulo="Cámaras operativas por núcleo", origen="real"),
                BloquePanel(tipo="eventos", titulo="Eventos con riesgo previsto", origen="modelo"),
                BloquePanel(
                    tipo="fuentes",
                    items=[
                        {"nombre": "Estado de las cámaras", "origen": "real"},
                        {"nombre": "Agenda municipal", "origen": "real"},
                    ],
                ),
            ],
            generado_en=datetime.now(UTC),
        )

    def _estado(self, **over):
        base = {
            "vertical_demo": dict.fromkeys(dp.FUENTE_VERTICAL, True),
            "contexto_demo": True,
            "social_demo": True,
            "actividad_mixta": True,
        }
        base.update(over)
        return dp.EstadoDatos(**base)

    def test_vertical_en_demo(self):
        p = dp.etiquetar(self._panel("seguridad"), self._estado())
        k = {x.etiqueta: x.origen for x in p.kpis}
        assert k["Cámaras online"] == "demo"
        assert k["Incidencias del mes"] == "ejemplo"  # el histórico conserva su origen
        assert k["Consumo del último mes"] == "real"  # dato real capturado de Datadis
        b = {x.titulo: x.origen for x in p.bloques if x.titulo}
        assert b["Cámaras operativas por núcleo"] == "demo"
        assert b["Eventos con riesgo previsto"] == "modelo"  # sale de la agenda, no de la vertical
        fuentes = {it["nombre"]: it["origen"] for it in p.bloques[-1].items}
        assert fuentes == {"Estado de las cámaras": "demo", "Agenda municipal": "real"}
        assert p.aviso and "FD-012" in p.aviso

    def test_vertical_integrada_no_se_marca(self):
        demo = {v: v != "seguridad" for v in dp.FUENTE_VERTICAL}
        p = dp.etiquetar(self._panel("seguridad"), self._estado(vertical_demo=demo))
        assert {x.etiqueta: x.origen for x in p.kpis}["Cámaras online"] == "real"
        assert p.aviso is None

    def test_contexto_sintetico_y_actividad_mixta(self):
        p = dp.etiquetar(self._panel("turismo"), self._estado())
        k = {x.etiqueta: x.origen for x in p.kpis}
        assert k["Pernoctaciones"] == "demo"
        assert k["Usos de tótems"] == "mixto"
        p = dp.etiquetar(
            self._panel("turismo"), self._estado(contexto_demo=False, actividad_mixta=False)
        )
        k = {x.etiqueta: x.origen for x in p.kpis}
        assert k["Pernoctaciones"] == "real" and k["Usos de tótems"] == "real"

    def test_eventos_demo_identificables(self):
        urns = dp.urns_eventos_demo()
        assert urns and all(u.startswith("urn:ngsi-ld:EventoTuristico:") for u in urns)
