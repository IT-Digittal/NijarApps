"""Motor de chatbot generativo sobre la API de OpenAI (CHATBOT_ENGINE=openai).

Responde en lenguaje natural fundamentado en los datos internos de la
plataforma (grounding): FAQs municipales, recursos turísticos publicados y
próximos eventos de la agenda. El modelo recibe ese contexto en cada consulta
y tiene instrucciones de no inventar horarios, precios ni servicios.

Cadena de disponibilidad: si la API de OpenAI falla o no hay clave, delega en
el motor Rasa (que a su vez cae al léxico), de modo que el asistente del
tótem nunca queda inoperativo.
"""

from __future__ import annotations

import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import Settings, get_settings
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.faq import InteraccionChatbot, NivelConfianza
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.schemas.chatbot import ChatQueryIn, ChatResponseOut, FuenteRespuesta
from nijar_dti.services import chatbot_service as lexical

log = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

IDIOMA_NOMBRE = {"es": "español", "en": "inglés", "de": "alemán", "fr": "francés"}


def _instrucciones(idioma: str) -> str:
    return (
        "Eres el asistente turístico oficial del Ayuntamiento de Níjar (Almería), "
        "instalado en un tótem interactivo del destino Cabo de Gata-Níjar. "
        f"Responde SIEMPRE en {IDIOMA_NOMBRE.get(idioma, 'español')}, en tono cercano y claro, "
        "en un máximo de 4 frases (es una pantalla táctil pública). "
        "Usa el CONTEXTO proporcionado como fuente principal; puedes complementar con "
        "conocimiento general del destino (geografía, naturaleza, cultura almeriense). "
        "NUNCA inventes horarios, precios, teléfonos ni servicios que no estén en el contexto: "
        "si no tienes el dato, dilo y recomienda consultar en la Oficina de Turismo. "
        "Si la pregunta no tiene relación con el turismo o los servicios de Níjar, "
        "indica amablemente que solo puedes ayudar con el destino."
    )


async def _contexto(db: AsyncSession, payload: ChatQueryIn) -> tuple[str, list[str]]:
    """Construye el contexto de grounding y devuelve (texto, intents_usados)."""
    partes: list[str] = []
    intents: list[str] = []

    # FAQs más afines a la pregunta (reutiliza el matching del motor léxico)
    faqs = await lexical._cargar_faqs_activas(db)
    campo_preg, campo_resp, _ = lexical._campos_idioma(payload.idioma)
    tokens_pregunta = lexical._tokenizar(payload.pregunta, payload.idioma)
    puntuadas = []
    for faq in faqs:
        preg = getattr(faq, campo_preg, None) or faq.pregunta_es
        sim = lexical._similitud(tokens_pregunta, lexical._tokenizar(preg or "", payload.idioma))
        if sim > 0.08:
            puntuadas.append((sim, faq))
    puntuadas.sort(key=lambda x: x[0], reverse=True)
    if puntuadas:
        partes.append("FAQs oficiales relacionadas:")
        for _, faq in puntuadas[:3]:
            resp = getattr(faq, campo_resp, None) or faq.respuesta_es
            partes.append(f"- P: {faq.pregunta_es}\n  R: {resp}")
            intents.append(faq.intent)

    # Recursos turísticos publicados (catálogo compacto)
    recursos = (
        await db.execute(
            select(RecursoTuristico)
            .where(RecursoTuristico.publicado.is_(True), RecursoTuristico.activo.is_(True))
            .limit(40)
        )
    ).scalars().all()
    if recursos:
        partes.append("Recursos turísticos del catálogo municipal (nombre · categoría · zona):")
        partes.extend(
            f"- {r.nombre} · {r.categoria} · {r.municipio}"
            + (f" · {r.descripcion_corta}" if r.descripcion_corta else "")
            for r in recursos
        )

    # Próximos eventos de la agenda
    from datetime import UTC, datetime

    eventos = (
        await db.execute(
            select(EventoTuristico)
            .where(
                EventoTuristico.publicado.is_(True),
                EventoTuristico.fecha_inicio >= datetime.now(UTC),
            )
            .order_by(EventoTuristico.fecha_inicio)
            .limit(6)
        )
    ).scalars().all()
    if eventos:
        partes.append("Próximos eventos de la agenda oficial:")
        partes.extend(
            f"- {e.nombre} · {e.fecha_inicio:%d/%m %H:%M}"
            + (f" · {e.direccion}" if e.direccion else "")
            for e in eventos
        )

    return "\n".join(partes), intents


async def _llamada_openai(settings: Settings, mensajes: list[dict]) -> tuple[str, dict]:
    """Llama a Chat Completions y devuelve (texto, uso de tokens)."""
    async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
        resp = await client.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": mensajes,
                "temperature": 0.3,
                "max_tokens": settings.openai_max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    texto = (data["choices"][0]["message"]["content"] or "").strip()
    return texto, data.get("usage") or {}


async def consultar_openai(
    db: AsyncSession,
    payload: ChatQueryIn,
    settings: Settings | None = None,
) -> ChatResponseOut:
    """Consulta al modelo de OpenAI con grounding y persiste la interacción."""
    settings = settings or get_settings()
    inicio = time.perf_counter()

    if not settings.openai_api_key:
        log.warning("CHATBOT_ENGINE=openai sin OPENAI_API_KEY — usando fallback")
        return await _fallback(db, payload, settings)

    try:
        contexto, intents = await _contexto(db, payload)
        mensajes = [
            {"role": "system", "content": _instrucciones(payload.idioma)},
            {
                "role": "system",
                "content": f"CONTEXTO:\n{contexto}" if contexto else "CONTEXTO: (sin datos)",
            },
            {"role": "user", "content": payload.pregunta},
        ]
        respuesta_texto, uso = await _llamada_openai(settings, mensajes)
        if not respuesta_texto:
            raise ValueError("respuesta vacía del modelo")
    except Exception as exc:  # noqa: BLE001 — cualquier fallo degrada al siguiente motor
        log.warning("OpenAI no disponible (%s) — usando fallback", exc)
        return await _fallback(db, payload, settings)

    # Confianza: alta si hubo FAQs afines en el contexto, media en caso contrario
    nivel = NivelConfianza.ALTA if intents else NivelConfianza.MEDIA
    score = 0.9 if intents else 0.6
    intent = intents[0] if intents else None

    fuentes = [
        FuenteRespuesta(
            tipo="openai",
            referencia=settings.openai_model,
            descripcion="Respuesta generada por IA con datos oficiales de la plataforma",
        )
    ] + [
        FuenteRespuesta(tipo="faq", referencia=i, descripcion="FAQ municipal usada como contexto")
        for i in intents[:3]
    ]

    latencia_ms = int((time.perf_counter() - inicio) * 1000)
    interaccion = InteraccionChatbot(
        sesion_id=payload.sesion_id,
        canal=payload.canal,
        idioma=payload.idioma,
        pregunta=payload.pregunta,
        respuesta=respuesta_texto,
        intent_detectado=intent,
        nivel_confianza=nivel.value,
        score_confianza=score,
        fuentes=[f.model_dump() for f in fuentes],
        latencia_ms=latencia_ms,
    )
    db.add(interaccion)
    await db.flush()
    await db.refresh(interaccion)

    # Registro de consumo para el control de costes del panel
    from nijar_dti.services import consumo_ia_service

    try:
        await consumo_ia_service.registrar(
            db,
            modelo=settings.openai_model,
            servicio="chatbot",
            canal=payload.canal,
            idioma=payload.idioma,
            tokens_entrada=int(uso.get("prompt_tokens") or 0),
            tokens_salida=int(uso.get("completion_tokens") or 0),
            latencia_ms=latencia_ms,
            interaccion_id=interaccion.id,
        )
    except Exception:  # noqa: BLE001 — el registro de costes nunca rompe la respuesta
        log.warning("No se pudo registrar el consumo de IA", exc_info=True)

    return ChatResponseOut(
        interaccion_id=interaccion.id,
        respuesta=respuesta_texto,
        intent_detectado=intent,
        nivel_confianza=nivel.value,
        score_confianza=score,
        fuentes=fuentes,
        sugerencias=None,
        latencia_ms=latencia_ms,
    )


async def _fallback(
    db: AsyncSession, payload: ChatQueryIn, settings: Settings
) -> ChatResponseOut:
    """Degrada a Rasa (que a su vez cae al léxico) para no dejar el tótem mudo."""
    from nijar_dti.services import chatbot_rasa_adapter

    try:
        return await chatbot_rasa_adapter.consultar_rasa(db, payload, settings=settings)
    except Exception:  # noqa: BLE001
        return await lexical.consultar(db, payload)
