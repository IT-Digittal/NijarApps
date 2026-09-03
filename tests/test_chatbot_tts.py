"""Tests de la síntesis de voz del chatbot (servicio y esquema)."""

from __future__ import annotations

import pytest

from nijar_dti.schemas.chatbot import TTSIn
from nijar_dti.services.chatbot_tts_service import (
    INSTRUCCIONES_POR_IDIOMA,
    TTSNoDisponibleError,
    sintetizar,
    tts_configurado,
)


class TestInstrucciones:
    def test_cuatro_idiomas_del_destino(self):
        assert set(INSTRUCCIONES_POR_IDIOMA) == {"es", "en", "de", "fr"}

    def test_acento_para_castellano(self):
        # La petición del Ayuntamiento: voz natural con acento andaluz/castellano
        es = INSTRUCCIONES_POR_IDIOMA["es"].lower()
        assert "andaluz" in es and "castellano" in es


class TestSintetizar:
    async def test_sin_clave_degrada(self):
        # En el entorno de tests no hay OPENAI_API_KEY: el servicio lo señala
        # con la excepción específica y el tótem usa la voz del navegador.
        assert tts_configurado() is False
        with pytest.raises(TTSNoDisponibleError):
            await sintetizar("Hola, bienvenido a Níjar", "es")


class TestTTSIn:
    def test_valido(self):
        p = TTSIn(texto="Las mejores playas son Mónsul y Genoveses")
        assert p.idioma == "es" and p.canal == "totem"

    def test_idioma_no_soportado(self):
        with pytest.raises(ValueError):
            TTSIn(texto="Hola", idioma="it")

    def test_texto_demasiado_largo(self):
        with pytest.raises(ValueError):
            TTSIn(texto="x" * 801)
