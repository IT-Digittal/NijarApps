"""Tests del conector Google Analytics 4 en modo dry-run."""

from __future__ import annotations

import asyncio

import pytest

from nijar_dti.config import Settings
from nijar_dti.connectors.analytics.ga4 import (
    GA4ChannelBreakdown,
    GA4Connector,
    GA4ConnectorError,
    GA4Overview,
    _overview_sintetico,
)


def _settings(**kwargs) -> Settings:
    base = {
        "secret_key": "test-secret-key-with-enough-entropy-1234567890",
        "database_url": "postgresql+asyncpg://x:x@localhost/x",
    }
    base.update(kwargs)
    return Settings(**base)


class TestIsConfigured:
    def test_no_configurado_por_defecto(self):
        c = GA4Connector(_settings())
        assert c.is_configured is False

    def test_configurado(self):
        c = GA4Connector(
            _settings(
                ga4_property_id="123456789",
                ga4_service_account_json='{"type":"service_account","client_email":"x"}',
            )
        )
        assert c.is_configured is True


class TestDryRun:
    def test_overview_sin_credenciales_devuelve_sintetico(self):
        c = GA4Connector(_settings())
        result = asyncio.run(c.overview(days_back=30))
        assert isinstance(result, GA4Overview)
        assert result.sesiones > 0
        assert result.usuarios > 0
        assert 0 <= result.bounce_rate <= 1

    def test_channels_sin_credenciales_devuelve_sintetico(self):
        c = GA4Connector(_settings())
        result = asyncio.run(c.channels_breakdown(days_back=30))
        assert isinstance(result, list)
        assert len(result) > 0
        for r in result:
            assert isinstance(r, GA4ChannelBreakdown)
            assert r.canal
            assert r.sesiones >= 0

    def test_overview_factor_dias(self):
        # Factor proporcional a los días solicitados
        ov_30 = _overview_sintetico(30)
        ov_60 = _overview_sintetico(60)
        assert ov_60.sesiones > ov_30.sesiones


class TestServiceAccountLoader:
    def test_carga_json_inline(self, tmp_path):
        c = GA4Connector(
            _settings(
                ga4_property_id="x",
                ga4_service_account_json='{"type":"service_account","client_email":"x"}',
            )
        )
        data = c._load_service_account()
        assert data["type"] == "service_account"

    def test_carga_desde_fichero(self, tmp_path):
        sa_file = tmp_path / "sa.json"
        sa_file.write_text('{"type":"service_account","client_email":"y"}')
        c = GA4Connector(
            _settings(
                ga4_property_id="x",
                ga4_service_account_json=str(sa_file),
            )
        )
        data = c._load_service_account()
        assert data["client_email"] == "y"

    def test_error_si_json_invalido(self):
        c = GA4Connector(
            _settings(
                ga4_property_id="x",
                ga4_service_account_json="no-es-json-ni-fichero",
            )
        )
        with pytest.raises(GA4ConnectorError):
            c._load_service_account()

    def test_error_si_no_configurado(self):
        c = GA4Connector(_settings())
        with pytest.raises(GA4ConnectorError):
            c._load_service_account()
