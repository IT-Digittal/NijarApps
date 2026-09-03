"""Síntesis de voz natural para el chatbot del tótem (OpenAI TTS).

Sustituye la voz robótica del sintetizador del navegador (eSpeak en los
tótems Linux) por un modelo de voz neuronal. Las instrucciones de estilo
fijan un acento castellano con calidez andaluza para el español y acentos
nativos para el resto de idiomas del destino.

Las respuestas del chatbot se repiten mucho (FAQs), así que se cachean los
audios en memoria (LRU) para no pagar dos veces la misma frase.
"""

from __future__ import annotations

from collections import OrderedDict

import httpx

from nijar_dti.config import get_settings

_URL = "https://api.openai.com/v1/audio/speech"
_MAX_CARACTERES = 800
_CACHE_MAX = 128

# Estilo de locución por idioma (gpt-4o-mini-tts admite instrucciones)
INSTRUCCIONES_POR_IDIOMA: dict[str, str] = {
    "es": (
        "Habla en castellano de España, con un acento andaluz suave y natural, "
        "como una guía turística cercana y cálida de Almería. Ritmo tranquilo, "
        "pronunciación clara, sin sonar robótica ni impostada."
    ),
    "en": (
        "Speak natural British English with the warm, friendly tone of a local "
        "tourist guide. Calm pace and clear pronunciation."
    ),
    "de": (
        "Sprich natürliches Hochdeutsch im warmen, freundlichen Ton einer "
        "örtlichen Reiseführerin. Ruhiges Tempo, klare Aussprache."
    ),
    "fr": (
        "Parle un français naturel, avec le ton chaleureux et accueillant d'une "
        "guide touristique locale. Rythme calme, prononciation claire."
    ),
}


class TTSError(Exception):
    """Error de dominio de la síntesis de voz."""


class TTSNoDisponibleError(TTSError):
    """No hay clave de OpenAI configurada: el tótem usará la voz del navegador."""


_cache: OrderedDict[tuple[str, str], bytes] = OrderedDict()


def tts_configurado() -> bool:
    return bool(get_settings().openai_api_key)


def _cachear(clave: tuple[str, str], audio: bytes) -> None:
    _cache[clave] = audio
    _cache.move_to_end(clave)
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)


async def sintetizar(texto: str, idioma: str = "es") -> bytes:
    """Devuelve el audio MP3 de ``texto`` con voz natural.

    Lanza ``TTSNoDisponibleError`` si no hay clave de OpenAI (el frontend
    degrada a la voz del navegador) y ``TTSError`` ante fallos de la API.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise TTSNoDisponibleError("OPENAI_API_KEY sin configurar")

    texto = texto.strip()[:_MAX_CARACTERES]
    if not texto:
        raise TTSError("Texto vacío")
    idioma = idioma if idioma in INSTRUCCIONES_POR_IDIOMA else "es"

    clave = (idioma, texto)
    if clave in _cache:
        _cache.move_to_end(clave)
        return _cache[clave]

    try:
        async with httpx.AsyncClient(timeout=max(settings.openai_timeout_seconds * 2, 30)) as cli:
            r = await cli.post(
                _URL,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_tts_model,
                    "voice": settings.openai_tts_voice,
                    "input": texto,
                    "instructions": INSTRUCCIONES_POR_IDIOMA[idioma],
                    "response_format": "mp3",
                },
            )
    except httpx.HTTPError as exc:
        raise TTSError(f"Fallo de red con el servicio de voz: {exc}") from exc
    if r.status_code != 200:
        raise TTSError(f"El servicio de voz respondió {r.status_code}")

    audio = r.content
    _cachear(clave, audio)
    return audio
