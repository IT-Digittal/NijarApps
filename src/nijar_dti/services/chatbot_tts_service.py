"""Síntesis de voz natural para el chatbot del tótem (OpenAI TTS).

Sustituye la voz robótica del sintetizador del navegador (eSpeak en los
tótems Linux) por un modelo de voz neuronal. Las instrucciones de estilo
fijan un acento castellano con calidez andaluza para el español y acentos
nativos para el resto de idiomas del destino.

Antes de sintetizar, el texto se adapta a la locución (``preparar_texto_voz``):
sin emojis, URLs, viñetas ni marcas de formato, que el modelo leería de forma
mecánica y hacen que la voz suene robótica.

Las respuestas del chatbot se repiten mucho (FAQs), así que se cachean los
audios en memoria (LRU) para no pagar dos veces la misma frase.
"""

from __future__ import annotations

import re
from collections import OrderedDict

import httpx

from nijar_dti.config import get_settings

_URL = "https://api.openai.com/v1/audio/speech"
_MAX_CARACTERES = 800
_CACHE_MAX = 128

# Estilo de locución por idioma (gpt-4o-mini-tts admite instrucciones).
# Se pide expresamente entonación conversacional, pausas naturales y variación
# melódica: sin ellas el modelo tiende a una lectura plana, "de locutora".
_ESTILO_COMUN_ES = (
    "Habla como una persona real conversando cara a cara con un visitante, no "
    "como si leyeras un texto. Entonación expresiva y variada, sonrisa en la voz, "
    "pausas breves y naturales entre frases y ritmo relajado pero ágil. Evita un "
    "tono monótono, mecánico o de anuncio."
)
INSTRUCCIONES_POR_IDIOMA: dict[str, str] = {
    "es": (
        "Eres una guía turística de Níjar (Almería), cercana y cálida. Habla en "
        "castellano de España con un deje andaluz suave y natural, sin exagerarlo. "
        + _ESTILO_COMUN_ES
    ),
    "en": (
        "You are a warm, friendly local tourist guide in Níjar, Almería. Speak "
        "natural British English as a real person chatting face to face with a "
        "visitor, not reading a script: expressive, varied intonation, a smile in "
        "the voice, short natural pauses and a relaxed pace. Never monotone or robotic."
    ),
    "de": (
        "Du bist eine herzliche, freundliche Reiseführerin aus Níjar (Almería). "
        "Sprich natürliches Hochdeutsch wie im persönlichen Gespräch mit einem Gast, "
        "nicht vorgelesen: lebendige, abwechslungsreiche Betonung, ein Lächeln in der "
        "Stimme, kurze natürliche Pausen, entspanntes Tempo. Nie monoton oder roboterhaft."
    ),
    "fr": (
        "Tu es une guide touristique de Níjar (Almería), chaleureuse et accueillante. "
        "Parle un français naturel, comme dans une vraie conversation avec un visiteur, "
        "sans lire : intonation expressive et variée, sourire dans la voix, courtes "
        "pauses naturelles, rythme détendu. Jamais monotone ni robotique."
    ),
}

# URL completa → solo su dominio ("https://www.nijar.es/turismo" → "nijar.es")
_RE_URL = re.compile(r"(?:https?://)?(?:www\.)([\w.-]+\.[a-z]{2,})\S*|https?://([\w.-]+)\S*", re.I)
# Emojis y pictogramas (planos suplementarios + símbolos varios + selectores)
_RE_EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U00002b00-\U00002bff"
    "\U0000fe0f\U0000200d\U000020e3]"
)
_RE_VINETA = re.compile(r"^\s*(?:[-*•·▪►✓]|\d+[.)])\s+", re.MULTILINE)
_RE_MARCAS = re.compile(r"[*_#`>|~]+")


def preparar_texto_voz(texto: str) -> str:
    """Adapta una respuesta escrita del asistente para leerla en voz alta.

    Reduce las URLs a su dominio y quita emojis, viñetas y marcas de formato (markdown) y
    convierte los saltos de línea y separadores en pausas de puntuación, para
    que la locución fluya como habla natural en lugar de leer símbolos.
    """
    t = _RE_URL.sub(lambda m: m.group(1) or m.group(2), texto)
    t = _RE_EMOJI.sub("", t)
    t = _RE_VINETA.sub("", t)
    t = _RE_MARCAS.sub("", t)
    t = t.replace(" · ", ", ").replace("·", ", ")
    # Cada línea es una frase: si no acaba en puntuación, se le añade un punto
    lineas = [ln.strip() for ln in t.splitlines() if ln.strip()]
    lineas = [ln if ln[-1] in ".!?…:;," else ln + "." for ln in lineas]
    t = " ".join(lineas)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,;:])(?=[,.;:])", "", t)
    return re.sub(r"\s{2,}", " ", t).strip()


class TTSError(Exception):
    """Error de dominio de la síntesis de voz."""


class TTSNoDisponibleError(TTSError):
    """No hay clave de OpenAI configurada: el tótem usará la voz del navegador."""


_cache: OrderedDict[tuple[str, str, str], bytes] = OrderedDict()


def tts_configurado() -> bool:
    return bool(get_settings().openai_api_key)


def _cachear(clave: tuple[str, str, str], audio: bytes) -> None:
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

    texto = preparar_texto_voz(texto)[:_MAX_CARACTERES]
    if not texto:
        raise TTSError("Texto vacío")
    idioma = idioma if idioma in INSTRUCCIONES_POR_IDIOMA else "es"

    clave = (settings.openai_tts_voice, idioma, texto)
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
