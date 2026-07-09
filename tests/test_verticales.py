"""Tests de las verticales Smart City (seeders + cableado de endpoints).

Los tests de seeders son unitarios (sin BBDD). Los de endpoints validan el
cableado (routing + auth): responden 401 sin token antes de tocar la BBDD.
"""

from __future__ import annotations

from nijar_dti.data.seeds.verticales import (
    ZONAS_ALUMBRADO,
    generar_camaras_seed,
    generar_contenedores_seed,
    generar_cuadros_seed,
    generar_luminarias_seed,
    generar_movilidad_seed,
    generar_sectores_agua_seed,
    generar_suministros_energia_seed,
)


class TestSeedAlumbrado:
    def test_zonas_suman_1240(self):
        assert len(ZONAS_ALUMBRADO) == 6
        assert sum(z["luminarias"] for z in ZONAS_ALUMBRADO) == 1240
        assert sum(z["led"] for z in ZONAS_ALUMBRADO) == 967
        assert sum(z["vsap"] for z in ZONAS_ALUMBRADO) == 211
        assert sum(z["solar"] for z in ZONAS_ALUMBRADO) == 62

    def test_luminarias_completas(self):
        lums = generar_luminarias_seed()
        assert len(lums) == 1240
        codigos = [x["codigo"] for x in lums]
        assert len(set(codigos)) == 1240
        tec = {"led": 0, "vsap": 0, "solar": 0}
        for x in lums:
            tec[x["tecnologia"]] += 1
        assert tec == {"led": 967, "vsap": 211, "solar": 62}
        # 17 averías + 10 sin comunicación
        assert sum(1 for x in lums if x["estado"] == "averia") == 17
        assert sum(1 for x in lums if x["estado"] == "sin_comunicacion") == 10

    def test_cuadros(self):
        cuadros = generar_cuadros_seed()
        assert len(cuadros) == 18
        por_code = {c["codigo"]: c for c in cuadros}
        assert por_code["CM-004"]["estado"] == "alerta"
        assert por_code["CM-013"]["estado"] == "sin_comunicacion"


class TestSeedResto:
    def test_agua(self):
        secs = generar_sectores_agua_seed()
        assert len(secs) == 14
        assert sum(s["contadores"] for s in secs) == 480
        assert sum(s["fugas_detectadas"] for s in secs) == 3

    def test_residuos(self):
        cont = generar_contenedores_seed()
        assert len(cont) == 684
        assert sum(1 for c in cont if c["tiene_sensor"]) == 412

    def test_movilidad(self):
        pts = generar_movilidad_seed()
        tipos = {p["tipo"] for p in pts}
        assert {"aforo", "parking", "recarga_ev", "lanzadera"} <= tipos

    def test_seguridad(self):
        cams = generar_camaras_seed()
        assert len(cams) == 24
        assert sum(1 for c in cams if c["estado"] == "sin_comunicacion") == 1

    def test_todos_los_activos_geoposicionables_llevan_coordenadas(self):
        """Sin coordenadas, los activos no aparecen en el gemelo ni en el mapa."""
        for coleccion in (
            generar_contenedores_seed(),
            generar_movilidad_seed(),
            generar_camaras_seed(),
        ):
            for item in coleccion:
                assert isinstance(item.get("latitud"), float), item.get("codigo")
                assert isinstance(item.get("longitud"), float), item.get("codigo")
                assert 36.5 < item["latitud"] < 37.2
                assert -2.5 < item["longitud"] < -1.8

    def test_energia(self):
        sums = generar_suministros_energia_seed()
        assert len(sums) == 61
        edificios = {s["edificio"].split(" (CUPS")[0] for s in sums}
        assert len(edificios) == 34
        assert all(s["cups"].startswith("ES") for s in sums)


class TestEndpointsWiring:
    def test_overviews_requieren_auth(self, client):
        for v in ("alumbrado", "agua", "residuos", "movilidad", "seguridad", "energia"):
            r = client.get(f"/api/v1/verticales/{v}/overview")
            assert r.status_code == 401, v

    def test_rutas_en_openapi(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        for p in (
            "/api/v1/verticales/alumbrado/overview",
            "/api/v1/verticales/alumbrado/luminarias",
            "/api/v1/verticales/alumbrado/cuadros",
            "/api/v1/verticales/agua/overview",
            "/api/v1/verticales/residuos/contenedores",
            "/api/v1/verticales/movilidad/overview",
            "/api/v1/verticales/seguridad/camaras",
            "/api/v1/verticales/energia/suministros",
        ):
            assert p in paths, p
