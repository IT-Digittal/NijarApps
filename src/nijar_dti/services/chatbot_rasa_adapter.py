"""Adapter del chatbot a Rasa Open Source.

Llama al servidor Rasa por HTTP (REST API) y traduce la respuesta al
modelo de salida ``ChatResponseOut`` de la plataforma. Si Rasa no está
disponible o devuelve un error, hace fallback al motor lexical baseline
del Hito 1 (configurable con ``RASA_FALLBACK_TO_LEXICAL``).

Flujo:

1. Llamada a ``POST /model/parse`` para obtener ``intent`` + confianza.
2. Llamada a ``POST /webhooks/rest/webhook`` para obtener el texto.
3. Persistencia de la interacción en BBDD para telemetría unificada.

Esta capa garantiza que los **endpoints del chatbot no cambien** entre el
motor lexical y Rasa: solo varía la fuente de la respuesta.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import Settings, get_settings
from nijar_dti.models.faq import InteraccionChatbot, NivelConfianza
from nijar_dti.schemas.chatbot import (
    ChatQueryIn,
    ChatResponseOut,
    FuenteRespuesta,
)
from nijar_dti.services import chatbot_service as lexical

# Re-exporta las funciones que no dependen del motor (feedback, intents,
# telemetría): siempre usan la BBDD, independientemente de Rasa o lexical.
registrar_feedback = lexical.registrar_feedback
listar_intents = lexical.listar_intents
telemetria = lexical.telemetria
telemetria_series = lexical.telemetria_series

log = logging.getLogger(__name__)


class RasaUnavailable(Exception):
    """Rasa no respondió o devolvió un error."""


async def _rasa_parse(client: httpx.AsyncClient, base_url: str, text: str) -> dict[str, Any]:
    resp = await client.post(f"{base_url}/model/parse", json={"text": text})
    if resp.status_code >= 400:
        raise RasaUnavailable(f"Rasa /model/parse {resp.status_code}: {resp.text[:200]}")
    return resp.json()


async def _rasa_webhook(
    client: httpx.AsyncClient, base_url: str, sender: str, text: str
) -> list[dict[str, Any]]:
    resp = await client.post(
        f"{base_url}/webhooks/rest/webhook",
        json={"sender": sender, "message": text},
    )
    if resp.status_code >= 400:
        raise RasaUnavailable(f"Rasa /webhooks/rest {resp.status_code}: {resp.text[:200]}")
    return resp.json() or []


def _intent_de_parse(parse: dict[str, Any]) -> tuple[str | None, float]:
    intent_obj = parse.get("intent") or {}
    return intent_obj.get("name"), float(intent_obj.get("confidence") or 0.0)


def _nivel_desde_confianza(score: float, fallback_threshold: float = 0.55) -> NivelConfianza:
    if score >= fallback_threshold + 0.20:  # ~0.75
        return NivelConfianza.ALTA
    if score >= fallback_threshold:
        return NivelConfianza.MEDIA
    return NivelConfianza.FUERA_DE_DOMINIO


async def consultar_rasa(
    db: AsyncSession,
    payload: ChatQueryIn,
    settings: Settings | None = None,
) -> ChatResponseOut:
    """Consulta a Rasa y persiste la interacción.

    Si Rasa falla y ``RASA_FALLBACK_TO_LEXICAL`` está activo (por defecto
    sí), delega en el motor lexical. Esto garantiza disponibilidad: el
    chatbot nunca queda inoperativo si el servidor Rasa cae.
    """
    settings = settings or get_settings()
    inicio = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.rasa_timeout_seconds) as client:
            parse = await _rasa_parse(client, settings.rasa_url, payload.pregunta)
            mensajes = await _rasa_webhook(
                client, settings.rasa_url, payload.sesion_id, payload.pregunta
            )
    except (httpx.HTTPError, RasaUnavailable) as exc:
        log.warning("Rasa no disponible: %s", exc)
        if settings.rasa_fallback_to_lexical:
            return await lexical.consultar(db, payload)
        raise

    intent_name, score = _intent_de_parse(parse)
    nivel = _nivel_desde_confianza(score)

    # Concatena los mensajes de texto que Rasa devuelve (puede haber varios)
    respuesta_texto = "\n".join(
        m.get("text", "").strip() for m in mensajes if m.get("text")
    ).strip()
    if not respuesta_texto:
        # Rasa no produjo respuesta → tratamos como fuera de dominio
        nivel = NivelConfianza.FUERA_DE_DOMINIO
        respuesta_texto = lexical._fuera_de_dominio_msg(payload.idioma)
        intent_name = None

    fuentes: list[FuenteRespuesta] | None = None
    if intent_name and nivel != NivelConfianza.FUERA_DE_DOMINIO:
        fuentes = [
            FuenteRespuesta(
                tipo="rasa",
                referencia=intent_name,
                descripcion="Respuesta generada por el modelo Rasa entrenado con FAQs municipales",
            )
        ]

    latencia_ms = int((time.perf_counter() - inicio) * 1000)

    interaccion = InteraccionChatbot(
        sesion_id=payload.sesion_id,
        canal=payload.canal,
        idioma=payload.idioma,
        pregunta=payload.pregunta,
        respuesta=respuesta_texto,
        intent_detectado=intent_name,
        nivel_confianza=nivel.value,
        score_confianza=round(float(score), 4),
        fuentes=[f.model_dump() for f in fuentes] if fuentes else None,
        latencia_ms=latencia_ms,
    )
    db.add(interaccion)
    await db.flush()
    await db.refresh(interaccion)

    sugerencias = (
        lexical._sugerencias_iniciales(payload.idioma)
        if nivel == NivelConfianza.FUERA_DE_DOMINIO
        else None
    )

    return ChatResponseOut(
        interaccion_id=interaccion.id,
        respuesta=respuesta_texto,
        intent_detectado=intent_name,
        nivel_confianza=nivel.value,
        score_confianza=round(float(score), 4),
        fuentes=fuentes,
        sugerencias=sugerencias,
        latencia_ms=latencia_ms,
    )


# ---------------- Selector de motor ----------------

async def consultar(db: AsyncSession, payload: ChatQueryIn) -> ChatResponseOut:
    """Punto de entrada unificado: respeta CHATBOT_ENGINE."""
    settings = get_settings()
    if settings.chatbot_engine == "rasa":
        return await consultar_rasa(db, payload, settings=settings)
    return await lexical.consultar(db, payload)
