"""Tests de los conectores Social Listening en modo dry-run.

No tocan APIs externas: validan el contrato del conector y que las
menciones sintéticas tienen el formato esperado.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from nijar_dti.config import Settings
from nijar_dti.connectors.social.facebook import FacebookConnector
from nijar_dti.connectors.social.instagram import InstagramConnector
from nijar_dti.connectors.social.twitter import TwitterConnector


def _settings_dry_run() -> Settings:
    """Construye un Settings con dry-run activado."""
    return Settings(
        secret_key="test-secret-key-with-enough-entropy-1234567890",
        database_url="postgresql+asyncpg://x:x@localhost/x",
        social_dry_run=True,
        social_listening_enabled=True,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTwitterConnector:
    def test_dry_run_devuelve_menciones(self):
        conn = TwitterConnector(_settings_dry_run())

        async def _get():
            return await conn.fetch_mentions(
                since=datetime.now(timezone.utc) - timedelta(hours=1)
            )
        menciones = asyncio.run(_get())
        assert len(menciones) > 0
        for m in menciones:
            assert m.fuente == "twitter_x"
            assert m.fuente_id_externo
            assert m.texto_original
            assert m.publicado_en.tzinfo is not None
            assert m.payload_original.get("dry_run") is True

    def test_is_configured_falso_sin_token(self):
        s = _settings_dry_run()
        conn = TwitterConnector(s)
        assert conn.is_configured is False

    def test_is_configured_verdadero_con_token(self):
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
            twitter_bearer_token="abc123",
        )
        conn = TwitterConnector(s)
        assert conn.is_configured is True

    def test_idiomas_variados(self):
        conn = TwitterConnector(_settings_dry_run())
        menciones = asyncio.run(conn.fetch_mentions())
        idiomas = {m.idioma for m in menciones}
        # las menciones sintéticas cubren los 4 idiomas obligatorios
        assert {"es", "en", "de", "fr"}.issubset(idiomas)


class TestFacebookConnector:
    def test_dry_run_devuelve_menciones(self):
        conn = FacebookConnector(_settings_dry_run())
        menciones = asyncio.run(conn.fetch_mentions())
        assert len(menciones) > 0
        for m in menciones:
            assert m.fuente == "facebook"
            assert m.fuente_id_externo
            assert m.texto_original

    def test_is_configured_falso_sin_credenciales(self):
        conn = FacebookConnector(_settings_dry_run())
        assert conn.is_configured is False

    def test_is_configured_verdadero_con_credenciales(self):
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
            facebook_access_token="abc",
            facebook_page_id="12345",
        )
        conn = FacebookConnector(s)
        assert conn.is_configured is True


class TestInstagramConnector:
    def test_dry_run_devuelve_menciones(self):
        conn = InstagramConnector(_settings_dry_run())
        menciones = asyncio.run(conn.fetch_mentions())
        assert len(menciones) > 0
        for m in menciones:
            assert m.fuente == "instagram"
            assert m.fuente_id_externo

    def test_hashtags_parsing(self):
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
            instagram_hashtags=" #cabodegata, nijar , #playamonsul ",
        )
        conn = InstagramConnector(s)
        assert conn.hashtags == ["cabodegata", "nijar", "playamonsul"]

    def test_is_configured(self):
        conn = InstagramConnector(_settings_dry_run())
        assert conn.is_configured is False
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
            facebook_access_token="abc",
            instagram_business_account_id="9999",
        )
        conn2 = InstagramConnector(s)
        assert conn2.is_configured is True
