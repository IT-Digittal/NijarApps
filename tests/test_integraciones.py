"""Tests del catálogo de fuentes de datos e integraciones + exportaciones CSV."""

from __future__ import annotations

from nijar_dti.data.seeds.fuentes_datos import FUENTES_DATOS_SEED


class TestSeedFuentes:
    def test_hay_propias_y_externas(self):
        origenes = {f["origen"] for f in FUENTES_DATOS_SEED}
        assert origenes == {"propia", "externa"}
        propias = [f for f in FUENTES_DATOS_SEED if f["origen"] == "propia"]
        externas = [f for f in FUENTES_DATOS_SEED if f["origen"] == "externa"]
        assert len(propias) >= 7
        assert len(externas) >= 10

    def test_codigos_unicos(self):
        cods = [f["codigo"] for f in FUENTES_DATOS_SEED]
        assert len(cods) == len(set(cods))

    def test_estados_validos(self):
        validos = {"operativa", "pendiente_desarrollo", "pendiente_acceso", "planificada"}
        for f in FUENTES_DATOS_SEED:
            assert f["estado"] in validos, f["codigo"]

    def test_externas_indican_credenciales(self):
        # Las fuentes externas deben documentar qué accesos hacen falta
        for f in FUENTES_DATOS_SEED:
            if f["origen"] == "externa" and f.get("requiere_credenciales"):
                assert f.get("credenciales_desc"), f["codigo"]

    def test_cubre_accesos_clave(self):
        blob = " ".join(f.get("credenciales_desc") or "" for f in FUENTES_DATOS_SEED).lower()
        for clave in ("ga4", "bearer token", "page access token", "instagram business", "dpd"):
            assert clave in blob, clave


class TestEndpointsWiring:
    def test_requieren_auth(self, client):
        for p in ("/api/v1/integraciones/fuentes", "/api/v1/integraciones/resumen"):
            assert client.get(p).status_code == 401, p

    def test_csv_requiere_auth(self, client):
        assert client.get("/api/v1/integraciones/fuentes.csv").status_code == 401
        assert client.get("/api/v1/verticales/alumbrado/luminarias.csv").status_code == 401

    def test_rutas_en_openapi(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        for p in (
            "/api/v1/integraciones/fuentes",
            "/api/v1/integraciones/resumen",
            "/api/v1/integraciones/fuentes.csv",
            "/api/v1/verticales/alumbrado/luminarias.csv",
            "/api/v1/verticales/energia/suministros.csv",
        ):
            assert p in paths, p
