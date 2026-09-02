"""Tests del comando de carga de capas geográficas (GeoJSON → geoportal)."""

from __future__ import annotations

import json

import pytest

from nijar_dti.data.cargar_capa import _nombre_elemento, geojson_a_wkt, leer_features
from nijar_dti.schemas.geografia import CapaGeograficaUpdate


class TestGeojsonAWkt:
    def test_point(self):
        assert geojson_a_wkt({"type": "Point", "coordinates": [-2.1, 36.9]}) == "POINT(-2.1 36.9)"

    def test_linestring(self):
        wkt = geojson_a_wkt({"type": "LineString", "coordinates": [[-2.1, 36.9], [-2.0, 36.95]]})
        assert wkt == "LINESTRING(-2.1 36.9, -2.0 36.95)"

    def test_polygon_con_anillo(self):
        wkt = geojson_a_wkt(
            {
                "type": "Polygon",
                "coordinates": [[[-2.1, 36.9], [-2.0, 36.9], [-2.0, 37.0], [-2.1, 36.9]]],
            }
        )
        assert wkt == "POLYGON((-2.1 36.9, -2.0 36.9, -2.0 37.0, -2.1 36.9))"

    def test_multipolygon(self):
        wkt = geojson_a_wkt(
            {
                "type": "MultiPolygon",
                "coordinates": [[[[-2.1, 36.9], [-2.0, 36.9], [-2.1, 36.9]]]],
            }
        )
        assert wkt == "MULTIPOLYGON(((-2.1 36.9, -2.0 36.9, -2.1 36.9)))"

    def test_tipo_no_soportado(self):
        with pytest.raises(ValueError, match="no soportado"):
            geojson_a_wkt({"type": "GeometryCollection", "coordinates": []})

    def test_geometria_incompleta(self):
        with pytest.raises(ValueError):
            geojson_a_wkt({"type": "Point"})


class TestLeerFeatures:
    def test_feature_collection(self, tmp_path):
        fichero = tmp_path / "capa.geojson"
        fichero.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [-2.1, 36.9]},
                            "properties": {"nombre": "A"},
                        },
                        {"type": "Feature", "geometry": None, "properties": {}},
                    ],
                }
            ),
            encoding="utf-8",
        )
        features = leer_features(fichero)
        # La feature sin geometría se descarta
        assert len(features) == 1
        assert features[0]["properties"]["nombre"] == "A"

    def test_fichero_no_geojson(self, tmp_path):
        fichero = tmp_path / "malo.json"
        fichero.write_text('{"hola": 1}', encoding="utf-8")
        with pytest.raises(ValueError, match="Feature"):
            leer_features(fichero)

    def test_sin_geometrias(self, tmp_path):
        fichero = tmp_path / "vacio.geojson"
        fichero.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
        with pytest.raises(ValueError, match="ninguna feature"):
            leer_features(fichero)


class TestNombreElemento:
    def test_usa_campo_indicado(self):
        assert _nombre_elemento({"rotulo_oficial": "Zona A"}, "rotulo_oficial", 0) == "Zona A"

    def test_fallbacks_habituales(self):
        assert _nombre_elemento({"name": "Sector 1"}, "nombre", 0) == "Sector 1"

    def test_sin_nombre(self):
        assert _nombre_elemento({}, "nombre", 4) == "Elemento 5"


class TestCapaGeograficaUpdate:
    def test_parcial(self):
        cambios = CapaGeograficaUpdate(activa=False)
        assert cambios.model_dump(exclude_unset=True) == {"activa": False}

    def test_color_valido(self):
        assert CapaGeograficaUpdate(color="#A1B2C3").color == "#A1B2C3"

    def test_color_invalido(self):
        with pytest.raises(ValueError):
            CapaGeograficaUpdate(color="rojo")

    def test_opacidad_fuera_de_rango(self):
        with pytest.raises(ValueError):
            CapaGeograficaUpdate(opacidad=1.5)
