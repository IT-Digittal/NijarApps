"""Normativa municipal: lectura de PDF, artículos, manifest, búsqueda y respuesta básica."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from nijar_dti.services import normativa_service as ns

PDF = Path(__file__).parent / "fixtures" / "ordenanza_comercio_ambulante_prueba.pdf"


class TestPdf:
    def test_extrae_texto_y_paginas(self):
        texto, paginas = ns.extraer_texto(PDF.read_bytes())
        assert paginas == 1
        assert "Artículo 12" in texto and "venta ambulante en las playas" in texto

    def test_limpia_guiones_y_espacios(self):
        assert (
            ns.limpiar_texto("ambu-\nlante   en\t\tla  playa\n\n\n\nfin")
            == "ambulante en la playa\n\nfin"
        )


class TestFragmentar:
    def test_por_articulos(self):
        texto, _ = ns.extraer_texto(PDF.read_bytes())
        frags = ns.fragmentar(texto)
        arts = [f.articulo for f in frags if f.articulo]
        assert "Artículo 12. Prohibiciones en playas" in arts
        assert frags[0].articulo is None  # título y exposición de motivos
        art12 = next(f for f in frags if f.articulo and f.articulo.startswith("Artículo 12"))
        assert "Parque Natural" in art12.texto and "Artículo 13" not in art12.texto

    def test_sin_articulos_en_trozos(self):
        texto = ("Frase de prueba sobre el mercadillo. " * 120).strip()
        frags = ns.fragmentar(texto)
        assert len(frags) > 1 and all(len(f.texto) <= ns.TAMANO_FRAGMENTO + 1 for f in frags)
        assert all(f.articulo is None for f in frags)

    def test_vacio(self):
        assert ns.fragmentar("   ") == []


class TestMetadatos:
    def test_titulo_y_tipo(self):
        assert ns.titulo_de_archivo("ORDENANZA_REGULADORA_DE_LA_CIRCULACION.pdf") == (
            "Ordenanza reguladora de la circulacion"
        )
        assert ns.tipo_de("edicto_provisional_ORDENANZA_FRACCIONAMIENTOS") == "edicto"
        assert ns.tipo_de("CERTIFICADO_EDICTO_Y_MODIFICACION_ORDENANZA") == "certificado"
        assert ns.tipo_de("Proyecto_Ordenanza_Fiscal") == "proyecto"
        assert ns.tipo_de("ORDENANZA_GENERAL_DE_CONTRIBUCIONES") == "ordenanza"
        assert ns.tipo_de("informe") == "otro"

    @pytest.mark.parametrize("sep", [",", ";"])
    def test_manifest(self, sep):
        csv = (
            f"Archivo{sep}Título{sep}URL{sep}Fecha\n"
            f"ORDENANZA_TAXI.pdf{sep}Ordenanza del servicio de taxi{sep}https://sede/x{sep}12/03/2019\n"
        ).encode()
        indice = ns.leer_manifest(csv)
        datos = ns.datos_de_manifest(indice["ORDENANZA_TAXI.pdf"])
        assert datos["titulo"] == "Ordenanza del servicio de taxi"
        assert datos["url"] == "https://sede/x" and str(datos["fecha"]) == "2019-03-12"

    def test_manifest_sin_columna_de_archivo(self):
        indice = ns.leer_manifest(b"nombre;enlace\nTaxi;docs/ORDENANZA_TAXI.pdf\n")
        assert "ORDENANZA_TAXI.pdf" in indice


class TestBusqueda:
    def test_terminos_de_una_pregunta(self):
        assert ns.terminos("¿Se puede vender en la playa de Níjar?") == ["vender", "playa"]
        assert ns.consulta_ts("¿Se puede vender en la playa?") == "vender:* | playa:*"
        assert ns.consulta_ts("¿Qué es esto?") is None

    def test_respuesta_basica(self, monkeypatch):
        monkeypatch.setattr(ns, "url_pdf", lambda i: f"/api/v1/normativa/{i}/pdf")
        p = ns.Pasaje(
            uuid4(),
            "Ordenanza reguladora del comercio ambulante",
            "Artículo 12. Prohibiciones en playas",
            "Artículo 12. Prohibiciones en playas\n"
            "Queda prohibida la venta ambulante en las playas.",
            0.23,
        )
        texto, fuentes = ns.respuesta_basica([p], "es")
        assert texto.startswith("Según la normativa municipal, «Ordenanza reguladora del comercio")
        assert "artículo 12 (Prohibiciones en playas)" in texto
        assert "Queda prohibida la venta ambulante" in texto
        assert fuentes[0].tipo == "normativa"

    def test_respuesta_basica_poco_relevante(self):
        p = ns.Pasaje(uuid4(), "X", None, "texto", 0.01)
        assert ns.respuesta_basica([p], "es") is None
        assert ns.respuesta_basica([], "es") is None


class TestRutas:
    @pytest.mark.parametrize("ruta", ["/api/v1/normativa", "/api/v1/normativa/resumen"])
    def test_requieren_auth(self, client, ruta):
        assert client.get(ruta).status_code == 401

    def test_importar_requiere_auth(self, client):
        assert client.post("/api/v1/normativa/importar").status_code == 401
