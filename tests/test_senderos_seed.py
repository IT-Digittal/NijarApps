"""Tests del seed de la red oficial de senderos de turismonijar.es."""

from __future__ import annotations

from nijar_dti.data.seeds.recursos_turisticos import RECURSOS_SEED
from nijar_dti.data.seeds.senderos import RECURSOS_SUSTITUIDOS, SENDEROS_SEED

IDIOMAS = {"es", "en", "de", "fr"}


class TestSenderosSeed:
    def test_red_completa(self):
        # S01–S16 + Camino de Santiago Argar Sureste
        assert len(SENDEROS_SEED) == 17

    def test_urns_unicos_y_estables(self):
        urns = [s["urn"] for s in SENDEROS_SEED]
        assert len(urns) == len(set(urns))
        for urn in urns:
            assert urn.startswith("urn:ngsi-ld:RecursoTuristico:nijar:sendero-")

    def test_sin_colision_con_recursos_previos(self):
        todos = [r["urn"] for r in RECURSOS_SEED]
        assert len(todos) == len(set(todos))

    def test_categoria_y_publicacion(self):
        for s in SENDEROS_SEED:
            assert s["categoria"] == "ruta", s["urn"]
            assert s["publicado"] is True, s["urn"]

    def test_i18n_completo_en_cuatro_idiomas(self):
        for s in SENDEROS_SEED:
            assert set(s["nombre_i18n"]) == IDIOMAS, s["urn"]
            assert set(s["descripcion_i18n"]) == IDIOMAS, s["urn"]
            for idioma in IDIOMAS:
                assert len(s["descripcion_i18n"][idioma]) > 40, (s["urn"], idioma)

    def test_coordenadas_dentro_de_nijar(self):
        for s in SENDEROS_SEED:
            assert 36.5 <= s["lat"] <= 37.1, s["urn"]
            assert -2.4 <= s["lon"] <= -1.8, s["urn"]

    def test_enlaces_oficiales(self):
        for s in SENDEROS_SEED:
            assert s["web"].startswith("https://turismonijar.es/"), s["urn"]
            gpx = s["enlaces_externos"].get("gpx")
            if gpx:
                assert gpx.startswith("https://turismonijar.es/rutas/") and gpx.endswith(".gpx")

    def test_ficha_tecnica_en_senderos_numerados(self):
        con_codigo = [
            s for s in SENDEROS_SEED if s["metadata_adicional"]["codigo_sendero"].startswith("S")
        ]
        assert len(con_codigo) == 16
        # Los S01–S15 traen ficha técnica completa de la web oficial
        for s in con_codigo:
            if s["metadata_adicional"]["codigo_sendero"] in {"S16"}:
                continue  # la web no publica ficha técnica del circuito S16
            for campo in ("longitud", "duracion", "dificultad", "trayecto"):
                assert campo in s["metadata_adicional"], (s["urn"], campo)

    def test_sustituidos_referencian_urns_existentes(self):
        urns = {r["urn"] for r in RECURSOS_SEED}
        for urn in RECURSOS_SUSTITUIDOS:
            assert urn in urns, urn
