"""Tests de gestión de roles dinámicos y del enforcement por permiso.

Unitarios (sin BBDD): validan la lógica pura del servicio de roles, que las
rutas están montadas y protegidas, y que los endpoints de verticales exigen
autenticación (el 403 por permiso restringido se cubre en el e2e con BBDD).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from nijar_dti.core import permisos
from nijar_dti.services import roles_service


class TestValidarPermisos:
    def test_ordena_y_deduplica(self):
        entrada = ["ver_agua", "ver_dti", "ver_agua"]
        assert roles_service._validar_permisos(entrada) == ["ver_agua", "ver_dti"]

    def test_rechaza_permiso_desconocido(self):
        with pytest.raises(roles_service.OperacionRolNoPermitidaError):
            roles_service._validar_permisos(["ver_agua", "ver_inexistente"])

    def test_todos_los_modulos_son_validos(self):
        ids = [m["id"] for m in permisos.MODULOS]
        assert roles_service._validar_permisos(ids) == sorted(ids)


class TestRutasRoles:
    def test_rutas_montadas(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/roles" in paths
        assert "/api/v1/roles/{slug}" in paths

    def test_listar_requiere_auth(self, client):
        assert client.get("/api/v1/roles").status_code == 401

    def test_crear_requiere_auth(self, client):
        resp = client.post("/api/v1/roles", json={"slug": "x_test", "display": "X", "permisos": []})
        assert resp.status_code == 401

    def test_editar_requiere_auth(self, client):
        assert client.patch("/api/v1/roles/auditor", json={"permisos": []}).status_code == 401

    def test_borrar_requiere_auth(self, client):
        assert client.delete(f"/api/v1/roles/rol_{uuid4().hex[:6]}").status_code == 401


class TestEnforcementVerticales:
    def test_vertical_requiere_auth(self, client):
        # Sin token: 401 (antes get_current_user, ahora require_permiso — sigue exigiendo auth).
        assert client.get("/api/v1/verticales/agua/overview").status_code == 401
        assert client.get("/api/v1/verticales/energia/overview").status_code == 401

    def test_dashboard_abierto_ahora_requiere_auth(self, client):
        assert client.get("/api/v1/dashboards/smart-office/overview").status_code == 401
