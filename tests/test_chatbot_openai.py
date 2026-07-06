"""Tests del motor generativo OpenAI del chatbot (sin BBDD ni red)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from nijar_dti.config import Settings
from nijar_dti.schemas.chatbot import ChatQueryIn
from nijar_dti.services import chatbot_openai_adapter as adapter


class FakeSession:
    """Sesión mínima: persiste en memoria y asigna id al refrescar."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def refresh(self, obj):
        obj.id = uuid4()


def _settings(**kw) -> Settings:
    return Settings(openai_api_key=kw.pop("openai_api_key", "sk-test"), **kw)


def _payload(**kw) -> ChatQueryIn:
    base = {"sesion_id": "test-1", "canal": "totem", "idioma": "es", "pregunta": "¿Qué playas hay?"}
    base.update(kw)
    return ChatQueryIn(**base)


class TestInstrucciones:
    def test_incluye_idioma_solicitado(self):
        assert "inglés" in adapter._instrucciones("en")
        assert "alemán" in adapter._instrucciones("de")

    def test_idioma_desconocido_cae_a_espanol(self):
        assert "español" in adapter._instrucciones("xx")

    def test_prohibe_inventar_datos(self):
        assert "inventes" in adapter._instrucciones("es")


class TestConsultarOpenai:
    async def test_respuesta_con_grounding(self, monkeypatch):
        async def fake_contexto(db, payload):
            return "FAQs oficiales relacionadas:\n- P: ¿Playas?", ["playas_destacadas"]

        async def fake_llamada(settings, mensajes):
            assert any(m["role"] == "user" for m in mensajes)
            assert "CONTEXTO" in mensajes[1]["content"]
            uso = {"prompt_tokens": 500, "completion_tokens": 60}
            return "Las playas más conocidas son Mónsul y Genoveses.", uso

        monkeypatch.setattr(adapter, "_contexto", fake_contexto)
        monkeypatch.setattr(adapter, "_llamada_openai", fake_llamada)

        out = await adapter.consultar_openai(FakeSession(), _payload(), settings=_settings())
        assert "Mónsul" in out.respuesta
        assert out.nivel_confianza == "alta"
        assert out.intent_detectado == "playas_destacadas"
        assert out.fuentes[0].tipo == "openai"
        assert any(f.tipo == "faq" for f in out.fuentes)

    async def test_sin_faqs_afines_nivel_media(self, monkeypatch):
        async def fake_contexto(db, payload):
            return "", []

        async def fake_llamada(settings, mensajes):
            return "Respuesta general del destino.", {}

        monkeypatch.setattr(adapter, "_contexto", fake_contexto)
        monkeypatch.setattr(adapter, "_llamada_openai", fake_llamada)

        out = await adapter.consultar_openai(FakeSession(), _payload(), settings=_settings())
        assert out.nivel_confianza == "media"
        assert out.intent_detectado is None

    async def test_sin_clave_usa_fallback(self, monkeypatch):
        llamado = {}

        async def fake_fallback(db, payload, settings):
            llamado["si"] = True
            return "FALLBACK"

        monkeypatch.setattr(adapter, "_fallback", fake_fallback)
        out = await adapter.consultar_openai(
            FakeSession(), _payload(), settings=_settings(openai_api_key="")
        )
        assert out == "FALLBACK"
        assert llamado.get("si")

    async def test_error_de_api_usa_fallback(self, monkeypatch):
        async def fake_contexto(db, payload):
            return "", []

        async def fake_llamada(settings, mensajes):
            raise RuntimeError("timeout simulado")

        async def fake_fallback(db, payload, settings):
            return "FALLBACK"

        monkeypatch.setattr(adapter, "_contexto", fake_contexto)
        monkeypatch.setattr(adapter, "_llamada_openai", fake_llamada)
        monkeypatch.setattr(adapter, "_fallback", fake_fallback)

        out = await adapter.consultar_openai(FakeSession(), _payload(), settings=_settings())
        assert out == "FALLBACK"


class TestConsumoIA:
    def test_coste_estimado_gpt4o_mini(self):
        from nijar_dti.services.consumo_ia_service import coste_estimado_usd

        # 1M de entrada a 0.15 + 1M de salida a 0.60
        assert coste_estimado_usd("gpt-4o-mini", 1_000_000, 1_000_000) == 0.75
        assert coste_estimado_usd("gpt-4o-mini", 0, 0) == 0.0

    def test_modelo_desconocido_usa_precio_defecto(self):
        from nijar_dti.services.consumo_ia_service import coste_estimado_usd

        assert coste_estimado_usd("modelo-futuro", 1_000_000, 0) == 0.5

    async def test_consulta_registra_consumo(self, monkeypatch):
        from nijar_dti.services import consumo_ia_service

        registros = []

        async def fake_registrar(db, **kw):
            registros.append(kw)

        async def fake_contexto(db, payload):
            return "", []

        async def fake_llamada(settings, mensajes):
            return "Respuesta.", {"prompt_tokens": 321, "completion_tokens": 45}

        monkeypatch.setattr(adapter, "_contexto", fake_contexto)
        monkeypatch.setattr(adapter, "_llamada_openai", fake_llamada)
        monkeypatch.setattr(consumo_ia_service, "registrar", fake_registrar)

        await adapter.consultar_openai(FakeSession(), _payload(), settings=_settings())
        assert len(registros) == 1
        assert registros[0]["tokens_entrada"] == 321
        assert registros[0]["tokens_salida"] == 45
        assert registros[0]["canal"] == "totem"
        assert registros[0]["servicio"] == "chatbot"


class TestConfig:
    def test_engine_openai_valido(self):
        s = Settings(chatbot_engine="openai")
        assert s.chatbot_engine == "openai"
        assert s.openai_model
        assert s.openai_timeout_seconds > 0

    def test_engine_invalido_rechazado(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(chatbot_engine="gemini")
