"""Tests de las capas geográficas del gemelo 2D (seed + esquemas GeoJSON)."""

from __future__ import annotations

from nijar_dti.data.seeds.capas_geograficas import _rect, generar_capas_seed
from nijar_dti.models.geografia import GrupoCapa, TipoGeometria
from nijar_dti.schemas.geografia import (
    CapaGeograficaOut,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)

GRUPOS_VALIDOS = {g.value for g in GrupoCapa}
TIPOS_VALIDOS = {t.value for t in TipoGeometria}


class TestSeedCapas:
    def test_capas_minimas(self):
        capas = generar_capas_seed()
        # Concepto «geoportal Níjar»: clasificación, calificación, ordenación,
        # partidos rurales y catastro.
        assert len(capas) >= 5

    def test_codigos_unicos(self):
        codigos = [c["codigo"] for c in generar_capas_seed()]
        assert len(codigos) == len(set(codigos))

    def test_grupos_y_tipos_validos(self):
        for c in generar_capas_seed():
            assert c["grupo"] in GRUPOS_VALIDOS, c["codigo"]
            assert c["tipo_geometria"] in TIPOS_VALIDOS, c["codigo"]

    def test_existe_capa_catastro(self):
        capas = {c["codigo"]: c for c in generar_capas_seed()}
        assert "catastro_parcelas" in capas
        assert capas["catastro_parcelas"]["grupo"] == GrupoCapa.CATASTRO

    def test_catastro_con_referencia(self):
        capas = {c["codigo"]: c for c in generar_capas_seed()}
        parcelas = capas["catastro_parcelas"]["elementos"]
        assert parcelas
        for p in parcelas:
            assert p.get("referencia_catastral"), p["nombre"]
            assert len(p["referencia_catastral"]) == 20

    def test_elementos_wkt_poligono(self):
        for c in generar_capas_seed():
            for e in c.get("elementos", []):
                assert e["wkt"].startswith("POLYGON(("), e["nombre"]

    def test_elementos_dentro_de_nijar(self):
        # Todas las geometrías demo caen en el bounding box del término municipal.
        for c in generar_capas_seed():
            for e in c.get("elementos", []):
                nums = e["wkt"].replace("POLYGON((", "").replace("))", "")
                for par in nums.split(","):
                    lon, lat = (float(x) for x in par.split())
                    assert -2.4 <= lon <= -1.8, e["nombre"]
                    assert 36.5 <= lat <= 37.1, e["nombre"]

    def test_todas_marcadas_como_demostracion(self):
        # No presentar cartografía de demo como oficial.
        for c in generar_capas_seed():
            assert "Demostración" in (c.get("fuente") or ""), c["codigo"]


class TestRect:
    def test_anillo_cerrado(self):
        wkt = _rect(-2.2, 36.9, 0.01, 0.01)
        coords = wkt.replace("POLYGON((", "").replace("))", "").split(",")
        # 5 vértices: el primero y el último coinciden (anillo cerrado).
        assert len(coords) == 5
        assert coords[0].strip() == coords[-1].strip()

    def test_centrado(self):
        from pytest import approx

        wkt = _rect(-2.0, 36.8, 0.02, 0.01)
        coords = [
            tuple(float(x) for x in p.split())
            for p in wkt.replace("POLYGON((", "").replace("))", "").split(",")
        ]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        assert min(lons) == approx(-2.02) and max(lons) == approx(-1.98)
        assert min(lats) == approx(36.79) and max(lats) == approx(36.81)


class TestEsquemasGeoJSON:
    def test_feature_por_defecto(self):
        f = GeoJSONFeature(geometry={"type": "Polygon", "coordinates": []})
        assert f.type == "Feature"
        assert f.properties == {}

    def test_feature_collection(self):
        capa = CapaGeograficaOut(
            id="00000000-0000-0000-0000-000000000001",
            codigo="x",
            nombre="X",
            grupo="catastro",
            tipo_geometria="poligono",
            color="#fff",
            color_borde="#000",
            opacidad=0.3,
            orden=0,
            activa=True,
        )
        fc = GeoJSONFeatureCollection(capa=capa, features=[])
        assert fc.type == "FeatureCollection"
        assert fc.capa.codigo == "x"
