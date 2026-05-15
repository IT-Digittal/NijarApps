"""Tests de los endpoints que pueden ejecutarse sin BBDD.

Validan rutas montadas, esquema OpenAPI generado y manejo de errores.
"""

from __future__ import annotations

import pytest


class TestOpenAPI:
    def test_openapi_disponible(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "Plataforma DTI Níjar"
        assert "paths" in data

    def test_paths_principales_montados(self, client):
        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]
        # Comprueba presencia de las rutas clave
        rutas_obligatorias = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/tourism/resources",
            "/api/v1/tourism/events",
            "/api/v1/tourism/services",
            "/api/v1/data/iot/ingest",
            "/api/v1/data/iot/sensors",
            "/api/v1/data/social/mentions",
            "/api/v1/data/social/kpis/sentiment",
            "/api/v1/data/social/kpis/share-of-voice",
            "/api/v1/data/social/topics",
            "/api/v1/cms/content",
            "/api/v1/cms/templates",
            "/api/v1/chatbot/query",
            "/api/v1/chatbot/feedback",
            "/api/v1/chatbot/intents",
            "/api/v1/chatbot/telemetry",
            "/api/v1/dashboards/smart-office/overview",
            "/api/v1/dashboards/smart-office/environment",
            "/api/v1/dashboards/big-data/overview",
            "/api/v1/dashboards/totems/usage",
            "/api/v1/dashboards/reports/monthly",
        ]
        for ruta in rutas_obligatorias:
            assert ruta in paths, f"Ruta esperada no encontrada: {ruta}"


class TestRootEndpoint:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert "name" in body
        assert "version" in body
        assert body["docs"] == "/docs"


class TestAuthErrores:
    def test_login_payload_invalido(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "no-email", "password": "1234"})
        # email mal formado o password muy corta
        assert resp.status_code == 422

    def test_logout_sin_token(self, client):
        resp = client.post("/api/v1/auth/logout")
        # sin token → 401
        assert resp.status_code == 401

    def test_me_sin_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_token_invalido(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 401


class TestErroresGlobales:
    def test_error_response_schema(self, client):
        """Las respuestas de error siguen el esquema APIError."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert body["code"] == "UNAUTHORIZED"

    def test_validation_error_schema(self, client):
        resp = client.post("/api/v1/auth/login", json={})  # falta email y password
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "message" in body
