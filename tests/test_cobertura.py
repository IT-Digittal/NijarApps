"""Tests de los endpoints de apoyo a las mediciones de cobertura (G-NetTrack)."""

from __future__ import annotations

import os

from nijar_dti.config import get_settings

_MIB = 1024 * 1024


class TestDescarga:
    def test_tamano_y_cabeceras(self, client):
        r = client.get("/api/v1/cobertura/descarga?mb=2")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/octet-stream"
        assert r.headers["content-length"] == str(2 * _MIB)
        assert "no-store" in r.headers["cache-control"]
        assert len(r.content) == 2 * _MIB

    def test_bytes_incompresibles(self, client):
        # Bytes aleatorios: una muestra no puede ser todo ceros
        r = client.get("/api/v1/cobertura/descarga?mb=1")
        assert r.content != b"\x00" * _MIB

    def test_limite_de_tamano(self, client):
        assert client.get("/api/v1/cobertura/descarga?mb=501").status_code == 422
        assert client.get("/api/v1/cobertura/descarga?mb=0").status_code == 422


class TestSubida:
    def test_post_binario_cuenta_bytes(self, client):
        cuerpo = os.urandom(3 * _MIB)
        r = client.post("/api/v1/cobertura/subida", content=cuerpo)
        assert r.status_code == 200
        datos = r.json()
        assert datos["ok"] is True
        assert datos["bytes"] == 3 * _MIB
        assert datos["megabytes"] == 3.0
        assert datos["duracion_ms"] >= 0

    def test_put_tambien_vale(self, client):
        r = client.put("/api/v1/cobertura/subida", content=b"x" * 1024)
        assert r.status_code == 200 and r.json()["bytes"] == 1024

    def test_multipart_tambien_vale(self, client):
        r = client.post("/api/v1/cobertura/subida", files={"fichero": ("p.bin", os.urandom(4096))})
        assert r.status_code == 200 and r.json()["bytes"] > 4096

    def test_rechaza_declaracion_gigante(self, client):
        r = client.post(
            "/api/v1/cobertura/subida",
            content=b"",
            headers={"Content-Length": str(2 * 1024 * _MIB)},
        )
        assert r.status_code == 413


class TestTokenOpcional:
    def test_token_exigido_solo_si_esta_definido(self, client):
        settings = get_settings()
        original = settings.cobertura_token
        try:
            settings.cobertura_token = "campo2026"
            assert client.get("/api/v1/cobertura/descarga?mb=1").status_code == 401
            assert client.post("/api/v1/cobertura/subida", content=b"x").status_code == 401
            assert client.get("/api/v1/cobertura/descarga?mb=1&k=campo2026").status_code == 200
            assert (
                client.post("/api/v1/cobertura/subida?k=campo2026", content=b"x").status_code == 200
            )
        finally:
            settings.cobertura_token = original


class TestPingYRegistro:
    def test_ping(self, client):
        r = client.get("/api/v1/cobertura/ping")
        assert r.status_code == 200 and r.json()["ok"] is True

    def test_registro_requiere_sesion(self, client):
        assert client.get("/api/v1/cobertura/registro").status_code in (401, 403)
