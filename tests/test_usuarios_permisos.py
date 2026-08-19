"""Tests de la matriz de permisos y de los endpoints de usuarios.

Son unitarios (no requieren BBDD): validan la lógica pura de `core.permisos`
y que las rutas de gestión de usuarios están montadas y protegidas.
"""

from __future__ import annotations

from uuid import uuid4

from nijar_dti.core import permisos
from nijar_dti.models.usuario import RolUsuario


class TestMatrizPermisos:
    def test_todos_los_roles_tienen_entrada(self):
        for rol in RolUsuario:
            assert rol.value in permisos.PERMISOS_POR_ROL
            assert rol.value in permisos.DISPLAY_ROLES

    def test_superadmin_tiene_todos_los_modulos(self):
        ids = {m["id"] for m in permisos.MODULOS}
        assert permisos.permisos_de(RolUsuario.ADMINISTRADOR_TIC.value) == ids

    def test_direccion_es_perfil_ejecutivo(self):
        p = permisos.permisos_de(RolUsuario.DIRECCION_GOBIERNO.value)
        # Ve resúmenes, recomendaciones e informes...
        assert "ver_resumen_municipal" in p
        assert "ver_recomendaciones_ia" in p
        assert "generar_informes" in p
        # ...pero NO el detalle técnico ni la administración.
        assert "ver_detalle_tecnico" not in p
        assert "gestionar_incidencias" not in p
        assert "administrar_usuarios" not in p
        assert "configurar_integraciones" not in p

    def test_roles_con_permiso(self):
        con_resumen = permisos.roles_con("ver_resumen_municipal")
        assert RolUsuario.DIRECCION_GOBIERNO.value in con_resumen
        assert RolUsuario.ADMINISTRADOR_TIC.value in con_resumen
        # Operaciones no tiene el resumen municipal directivo.
        assert RolUsuario.OPERADOR_SMART_OFFICE.value not in con_resumen

        # administrar_usuarios solo lo tiene el superadministrador.
        assert permisos.roles_con("administrar_usuarios") == (RolUsuario.ADMINISTRADOR_TIC.value,)

    def test_permisos_solo_referencian_modulos_conocidos(self):
        ids = {m["id"] for m in permisos.MODULOS}
        for concedidos in permisos.PERMISOS_POR_ROL.values():
            assert concedidos <= ids

    def test_matriz_serializable(self):
        m = permisos.matriz()
        assert m["modulos"] == permisos.MODULOS
        assert len(m["roles"]) == len(RolUsuario)
        primera = m["roles"][0]
        assert {"rol", "display", "permisos"} <= primera.keys()


class TestEndpointsUsuarios:
    def test_rutas_montadas(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/usuarios" in paths
        assert "/api/v1/usuarios/matriz-permisos" in paths
        assert "/api/v1/usuarios/{usuario_id}" in paths
        assert "/api/v1/usuarios/{usuario_id}/activar" in paths
        assert "/api/v1/usuarios/{usuario_id}/desactivar" in paths
        assert "/api/v1/usuarios/{usuario_id}/reset-password" in paths

    def test_matriz_requiere_autenticacion(self, client):
        resp = client.get("/api/v1/usuarios/matriz-permisos")
        assert resp.status_code == 401

    def test_editar_requiere_autenticacion(self, client):
        resp = client.patch(f"/api/v1/usuarios/{uuid4()}", json={"activo": False})
        assert resp.status_code == 401

    def test_eliminar_requiere_autenticacion(self, client):
        resp = client.delete(f"/api/v1/usuarios/{uuid4()}")
        assert resp.status_code == 401
