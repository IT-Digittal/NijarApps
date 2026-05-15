"""Configuración común para los tests.

La suite se divide en dos grupos:

- **Unitarios** (default): no requieren BBDD; validan schemas, lógica del
  chatbot, helpers y routers de salud. Son rápidos y se ejecutan en CI.
- **Integración** (marcador `integration`): requieren PostgreSQL + PostGIS
  corriendo (vía `docker compose up -d db`). Se ejecutan con
  `pytest -m integration`.
"""

from __future__ import annotations

import os

# Variables de entorno mínimas para que se pueda importar la app en tests
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-enough-entropy-for-tests-1234")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://nijar:nijar@localhost:5432/nijar_dti")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("CORS_ORIGINS", "")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """Aplicación FastAPI en modo test."""
    from nijar_dti.main import app as fastapi_app

    return fastapi_app


@pytest.fixture()
def client(app):
    """Cliente de pruebas síncrono (TestClient)."""
    with TestClient(app) as c:
        yield c
