"""Tests de los documentos adjuntos a puntos del territorio."""

from __future__ import annotations

import pytest

from nijar_dti.schemas.documentos import TAMANO_MAX_BYTES, TIPOS_ENTIDAD_VALIDOS
from nijar_dti.services.documentos_service import (
    DocumentoError,
    _nombre_seguro,
    crear_documento,
)


class TestValidaciones:
    """Las validaciones fallan antes de tocar BBDD o disco (db=None)."""

    async def test_tipo_entidad_invalido(self):
        with pytest.raises(DocumentoError, match="no válido"):
            await crear_documento(
                None,  # type: ignore[arg-type]
                entidad_tipo="nave_espacial",
                entidad_id="x",
                entidad_nombre="X",
                latitud=None,
                longitud=None,
                nombre_archivo="a.pdf",
                tipo_mime="application/pdf",
                contenido=b"datos",
                descripcion=None,
                subido_por=None,
            )

    async def test_fichero_vacio(self):
        with pytest.raises(DocumentoError, match="vacío"):
            await crear_documento(
                None,  # type: ignore[arg-type]
                entidad_tipo="recurso",
                entidad_id="x",
                entidad_nombre="X",
                latitud=None,
                longitud=None,
                nombre_archivo="a.pdf",
                tipo_mime=None,
                contenido=b"",
                descripcion=None,
                subido_por=None,
            )

    async def test_fichero_demasiado_grande(self):
        with pytest.raises(DocumentoError, match="máximo"):
            await crear_documento(
                None,  # type: ignore[arg-type]
                entidad_tipo="recurso",
                entidad_id="x",
                entidad_nombre="X",
                latitud=None,
                longitud=None,
                nombre_archivo="a.bin",
                tipo_mime=None,
                contenido=b"0" * (TAMANO_MAX_BYTES + 1),
                descripcion=None,
                subido_por=None,
            )


def test_nombre_seguro_sanea_rutas_y_control():
    assert _nombre_seguro("../../etc/passwd") == ".._.._etc_passwd"
    assert _nombre_seguro("ficha técnica v2.pdf") == "ficha técnica v2.pdf"
    assert _nombre_seguro("a\\b\x00c.txt") == "a_b_c.txt"
    assert _nombre_seguro("") == "documento"
    assert len(_nombre_seguro("x" * 400)) == 255


def test_tipos_entidad_cubren_todas_las_capas_del_gemelo():
    assert {
        "recurso",
        "sensor",
        "cuadro",
        "contenedor",
        "movilidad",
        "camara",
        "bandera",
        "estacion_aire",
    } <= TIPOS_ENTIDAD_VALIDOS


class TestRutasApi:
    def test_endpoints_en_openapi_con_autenticacion(self, client):
        spec = client.get("/openapi.json").json()
        rutas = spec["paths"]
        assert "/api/v1/documentos" in rutas
        assert "/api/v1/documentos/{doc_id}/archivo" in rutas
        # La descarga exige sesión (los documentos pueden ser internos)
        assert rutas["/api/v1/documentos/{doc_id}/archivo"]["get"].get("security")
        # La subida exige rol de gestión
        assert rutas["/api/v1/documentos"]["post"].get("security")
