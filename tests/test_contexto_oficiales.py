"""Conectores reales de INE, Junta (IECA) y AENA: parseo de sus formatos, sin red."""

from __future__ import annotations

import io

import openpyxl
import pytest

from nijar_dti.connectors.contexto import fuentes, oficiales
from nijar_dti.connectors.contexto.oficiales import PuntoMensual
from nijar_dti.services import direccion_panel_service as dp


class TestINE:
    def test_formato_inebase(self):
        datos = [
            {"T3_Periodo": "M09", "Anyo": 2026, "Valor": 728942.0, "T3_TipoDato": "Provisional"},
            {"T3_Periodo": "M08", "Anyo": 2026, "Valor": 900000.0, "T3_TipoDato": "Definitivo"},
        ]
        p = oficiales.puntos_ine(datos)
        assert [x.periodo for x in p] == ["2026-08", "2026-09"]
        assert p[1].provisional and not p[0].provisional

    def test_formato_tempus_y_escala(self):
        datos = [{"FK_Periodo": 8, "Anyo": 2026, "Valor": 2797.11, "Secreto": False}]
        assert oficiales.puntos_ine(datos, escala=1e6)[0].valor == pytest.approx(2_797_110_000)

    def test_descarta_secretos_y_vacios(self):
        datos = [
            {"FK_Periodo": 1, "Anyo": 2026, "Valor": None},
            {"FK_Periodo": 2, "Anyo": 2026, "Valor": 5, "Secreto": True},
            {"FK_Periodo": 19, "Anyo": 2026, "Valor": 5},  # periodo no mensual
        ]
        assert oficiales.puntos_ine(datos) == []

    def test_cae_a_inebase_si_tempus_no_responde(self, monkeypatch):
        import httpx

        class Resp:
            def __init__(self, url):
                self.url = url

            def raise_for_status(self):
                if "wstempus" in self.url:
                    raise httpx.HTTPStatusError("503", request=None, response=None)  # type: ignore[arg-type]

            def json(self):
                return [
                    {"COD": "EOT1460", "Data": [{"T3_Periodo": "M01", "Anyo": 2026, "Valor": 1}]}
                ]

        monkeypatch.setattr(httpx.Client, "get", lambda self, url, **k: Resp(url))
        assert oficiales.serie_ine("EOT1460", 2074, 12) == [PuntoMensual("2026-01", 1.0)]

    def test_trimestres_solo_completos(self):
        meses = [PuntoMensual(f"2026-{m:02d}", 1.0) for m in range(1, 9)]
        assert oficiales.trimestres(meses) == [("2026-Q1", 3.0, False), ("2026-Q2", 3.0, False)]


def _excel(hojas: dict[str, list[list]]) -> bytes:
    libro = openpyxl.Workbook()
    libro.remove(libro.active)
    for titulo, filas in hojas.items():
        hoja = libro.create_sheet(titulo)
        for f in filas:
            hoja.append(f)
    buf = io.BytesIO()
    libro.save(buf)
    return buf.getvalue()


class TestAENA:
    def test_formato_actual_ranking_mensual(self):
        filas = [
            ["TRÁFICO DE PASAJEROS, OPERACIONES Y CARGA EN LA RED DE AENA"],
            ["Datos provisionales", None, "Mensual: Septiembre de 2026"],
            [None, "Aeropuertos", "Total", "% Inc", None, "Aeropuertos", "Total"],
            [None, "ALMERÍA", 105225, 0.2, None, "LA PALMA", 2264],
            [None, "MELILLA", 44718, 0.1, None, "ALMERÍA", 1519],  # operaciones: se ignora
        ]
        contenido = _excel({"Ranking mensual": filas, "Ranking acumulado": filas})
        p = oficiales.leer_excel_aena(contenido, "Almería")
        assert p == PuntoMensual("2026-09", 105225.0, True)

    def test_formato_anterior_una_hoja_por_mes(self):
        contenido = _excel(
            {
                "FEBRERO 2023": [
                    [None, "TRÁFICO DE PASAJEROS", "FEBRERO DE 2023"],
                    [None, "DATOS DEFINITIVOS"],
                    [None, None, "ALMERÍA", 29234, 0.52],
                ],
                "ACUMULADO FEBRERO 2023": [
                    [None, "ACUMULADO A FEBRERO DE 2023"],
                    [None, None, "ALMERÍA", 54799, 0.5],
                ],
            }
        )
        assert oficiales.leer_excel_aena(contenido, "ALMERIA") == PuntoMensual(
            "2023-02", 29234.0, False
        )

    def test_enlaces_de_descarga(self):
        html = (
            '<a href="/sites/Satellite?blobcol=urldata&amp;blobwhere=1&amp;ssbinary=true">x</a>'
            '<a href="/sites/Satellite?blobcol=urldata&amp;blobwhere=1&amp;ssbinary=true">y</a>'
        )
        assert oficiales.enlaces_aena(html) == [
            "https://www.aena.es/sites/Satellite?blobcol=urldata&blobwhere=1&ssbinary=true"
        ]


class TestIECA:
    def test_meses_del_arbol(self):
        arbol = {
            "cod": "TOTAL",
            "children": [
                {
                    "cod": "2026",
                    "children": [{"id": 9, "cod": "202609"}, {"id": 8, "cod": "202608"}],
                },
                {"cod": "2070", "children": [{"id": 99, "cod": "207001"}]},
            ],
        }
        assert oficiales.meses_ieca(arbol, "202609", "202612") == {"202609": 9}

    def test_toma_el_total_de_residencias_y_categorias(self):
        def fila(res, cat, viajeros):
            return [
                {"cod": ["2026", "202609"]},
                {"cod": ["C01", "04"]},
                {"cod": res},
                {"cod": cat},
                {"val": str(viajeros)},
                {"val": "1"},
            ]

        filas = [
            fila(["00", "108"], ["00"], 1),
            fila(["00"], ["00", "01"], 2),
            fila(["00"], ["00"], 196868.0),
        ]
        assert oficiales.puntos_ieca(filas) == [PuntoMensual("2026-09", 196868, False)]


class TestRegistrosReales:
    def test_no_llevan_marca_sintetica(self, monkeypatch):
        monkeypatch.setattr(
            oficiales, "serie_ine", lambda *a, **k: [PuntoMensual("2026-09", 1.0, True)]
        )
        r = fuentes.INEEohConnector(dry_run=False).fetch_series(1)
        assert r[0].metadatos.get("sintetico") is None and r[0].metadatos["provisional"]
        assert r[0].metadatos["serie"] == "EOT1460"


class TestEtiquetadoPorFuente:
    def test_mezcla_de_series_reales_y_sinteticas(self):
        from datetime import UTC, datetime

        from nijar_dti.schemas.direccion import BloquePanel, HeroPanel, KpiPanel, PanelDireccion

        panel = PanelDireccion(
            modulo="turismo",
            titulo="t",
            intro="i",
            hero=HeroPanel(fondo="turismo", titulo="h", subtitulo="s"),
            kpis=[
                KpiPanel(etiqueta="Pernoctaciones", valor="1"),
                KpiPanel(etiqueta="Pasajeros AENA", valor="2"),
            ],
            bloques=[
                BloquePanel(tipo="barras_h", titulo="Indicadores oficiales frente al año pasado"),
                BloquePanel(
                    tipo="fuentes",
                    items=[
                        {"nombre": "AENA", "origen": "real"},
                        {"nombre": "Junta de Andalucía", "origen": "real"},
                    ],
                ),
            ],
            generado_en=datetime.now(UTC),
        )
        est = dp.EstadoDatos(
            vertical_demo={}, contexto_demo=True, contexto_fuentes_demo=frozenset({"aena"})
        )
        p = dp.etiquetar(panel, est)
        k = {x.etiqueta: x.origen for x in p.kpis}
        assert k == {"Pernoctaciones": "real", "Pasajeros AENA": "demo"}
        assert p.bloques[0].origen == "mixto"
        assert {i["nombre"]: i["origen"] for i in p.bloques[1].items} == {
            "AENA": "demo",
            "Junta de Andalucía": "real",
        }
