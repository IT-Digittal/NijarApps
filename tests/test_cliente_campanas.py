"""Tests de los módulos Ficha del cliente, Campañas y telemetría de tótems.

Los tests de endpoints validan el cableado (routing + auth) sin necesidad de
BBDD: las rutas protegidas responden 401 antes de tocar la base de datos.
Los tests de schemas y seeds son puramente unitarios.
"""

from __future__ import annotations

from datetime import UTC

import pytest
from pydantic import ValidationError

from nijar_dti.data.seeds.sensores import SENSORES_SEED
from nijar_dti.schemas.campanas import CampanaIn
from nijar_dti.schemas.cliente import ClienteIn


class TestEndpointsWiring:
    """Las rutas nuevas existen y exigen autenticación (401 sin token)."""

    def test_cliente_get_requiere_auth(self, client):
        assert client.get("/api/v1/cliente").status_code == 401

    def test_cliente_put_requiere_auth(self, client):
        assert client.put("/api/v1/cliente", json={"nombre": "X"}).status_code == 401

    def test_campanas_list_requiere_auth(self, client):
        assert client.get("/api/v1/campanas").status_code == 401

    def test_campanas_post_requiere_auth(self, client):
        assert client.post("/api/v1/campanas", json={}).status_code == 401

    def test_totems_health_requiere_auth(self, client):
        assert client.get("/api/v1/dashboards/totems/health").status_code == 401

    def test_rutas_en_openapi(self, client):
        spec = client.get("/openapi.json").json()
        assert "/api/v1/cliente" in spec["paths"]
        assert "/api/v1/campanas" in spec["paths"]
        assert "/api/v1/campanas/{campana_id}/kpis" in spec["paths"]
        assert "/api/v1/dashboards/totems/health" in spec["paths"]


class TestSchemas:
    def test_cliente_in_minimo(self):
        c = ClienteIn(nombre="Ayuntamiento de Níjar")
        assert c.municipio == "Níjar"
        assert c.provincia == "Almería"

    def test_campana_in_requiere_fechas(self):
        with pytest.raises(ValidationError):
            CampanaIn(nombre="Sin fechas")

    def test_campana_estado_invalido(self):
        from datetime import datetime

        with pytest.raises(ValidationError):
            CampanaIn(
                nombre="X",
                fecha_inicio=datetime(2026, 1, 1, tzinfo=UTC),
                fecha_fin=datetime(2026, 2, 1, tzinfo=UTC),
                estado="inexistente",
            )

    def test_campana_objetivo_valido(self):
        from datetime import datetime

        c = CampanaIn(
            nombre="Verano",
            fecha_inicio=datetime(2026, 6, 1, tzinfo=UTC),
            fecha_fin=datetime(2026, 9, 1, tzinfo=UTC),
            objetivo="sensibilizacion",
            estado="activa",
        )
        assert c.objetivo == "sensibilizacion"


class TestTotemSensoresSeed:
    def test_hay_sensores_de_tipo_totem(self):
        totems = [s for s in SENSORES_SEED if s["tipo"] == "totem"]
        # Un sensor de salud por cada tótem (Rodalquilar y Los Albaricoques)
        assert len(totems) >= 2

    def test_totem_sensores_tienen_umbral_temperatura(self):
        for s in SENSORES_SEED:
            if s["tipo"] == "totem":
                assert "temperatura_interna_max" in (s.get("umbrales_alerta") or {})
