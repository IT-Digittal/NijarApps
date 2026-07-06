"""Lógica de negocio del chatbot IA Asistente de Turismo de Níjar.

Esta primera versión implementa un motor de matching de intents basado en
similitud léxica sobre las frases de entrenamiento de las FAQs (cobertura
inicial ≥100 FAQs en los 4 idiomas obligatorios). El grounding sigue los
tres niveles definidos en la Memoria Técnica (alta, media, fuera de dominio).

La arquitectura permite sustituir el motor por Rasa o un LLM con RAG en el
Hito 2 sin modificar los endpoints ni los esquemas.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.faq import FAQ, InteraccionChatbot, NivelConfianza
from nijar_dti.schemas.chatbot import (
    ChatQueryIn,
    ChatResponseOut,
    ChatbotTelemetry,
    FuenteRespuesta,
    IntentInfo,
    TopIntentItem,
)
from nijar_dti.schemas.common import PuntoSerieDiaria, SerieDiaria


# Stop-words mínimas por idioma (suficientes para un motor lexical baseline).
_STOP_WORDS: dict[str, set[str]] = {
    "es": {
        "el","la","los","las","un","una","unos","unas","de","del","al","a","y","o",
        "que","como","cuando","donde","cual","cuales","es","son","esta","están",
        "para","por","con","sin","mi","mis","tu","tus","su","sus","me","te","se",
        "lo","yo","tú","él","ella","nosotros","vosotros","ellos","muy","más","menos",
        "poco","mucho","si","no","ni","pero","porque","qué","cómo","dónde","cuánto",
        "hola","buenas","buenos","tardes","días","favor","gracias","quiero","quería",
        "podría","puede","puedes","hay",
    },
    "en": {
        "the","a","an","of","and","or","to","in","on","at","by","for","with","without",
        "is","are","was","were","be","been","being","i","you","he","she","it","we","they",
        "my","your","his","her","its","our","their","this","that","these","those",
        "what","when","where","which","how","why","who","please","thanks","thank","hi",
        "hello","there","do","does","did","can","could","would","should","may","might",
    },
    "de": {
        "der","die","das","den","dem","des","ein","eine","einen","einem","eines",
        "und","oder","aber","auch","nicht","kein","keine","ich","du","er","sie","es",
        "wir","ihr","mich","dich","sich","mein","dein","sein","ihr","unser","euer",
        "ist","sind","war","waren","sein","werden","wird","kann","könnte","soll","muss",
        "wo","was","wann","wie","warum","wer","welche","welcher","welches",
        "bitte","danke","hallo","guten","tag","morgen",
    },
    "fr": {
        "le","la","les","un","une","des","de","du","au","aux","à","et","ou","mais",
        "ne","pas","ni","je","tu","il","elle","nous","vous","ils","elles","moi","toi",
        "lui","mon","ma","mes","ton","ta","tes","son","sa","ses","notre","votre","leur",
        "est","sont","était","étaient","être","avoir","peut","peux","pourrais","doit",
        "où","quand","comment","quoi","quel","quelle","quels","quelles","pourquoi",
        "qui","s'il","sil","please","merci","bonjour","bonsoir",
    },
}


_PALABRA_RE = re.compile(r"[\wáéíóúüñçàèìòùâêîôû]+", re.IGNORECASE | re.UNICODE)


# --- Umbrales del motor (ajustables) ---
UMBRAL_CONFIANZA_ALTA = 0.55
UMBRAL_CONFIANZA_MEDIA = 0.30


def _normalizar(texto: str) -> str:
    """Pasa a minúsculas y elimina acentos para comparación insensible."""
    texto = texto.lower().strip()
    nf = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nf if unicodedata.category(c) != "Mn")


def _tokenizar(texto: str, idioma: str) -> set[str]:
    stops = _STOP_WORDS.get(idioma, set())
    norm = _normalizar(texto)
    tokens = {t for t in _PALABRA_RE.findall(norm) if t and t not in stops and len(t) > 1}
    return tokens


def _similitud(a: set[str], b: set[str]) -> float:
    """Similitud Jaccard ponderada — robusta y sin dependencias externas."""
    if not a or not b:
        return 0.0
    inter = a & b
    union = a | b
    return len(inter) / len(union)


def _campos_idioma(idioma: str) -> tuple[str, str, str]:
    """Devuelve los nombres de columnas para (pregunta, frases_entrenamiento, respuesta)."""
    if idioma not in {"es", "en", "de", "fr"}:
        idioma = "es"
    return (f"pregunta_{idioma}", f"frases_entrenamiento_{idioma}", f"respuesta_{idioma}")


async def _cargar_faqs_activas(db: AsyncSession) -> list[FAQ]:
    res = await db.execute(
        select(FAQ).where(FAQ.activo.is_(True)).where(FAQ.deleted_at.is_(None))
    )
    return list(res.scalars().all())


def _buscar_mejor_intent(
    pregunta: str, idioma: str, faqs: Iterable[FAQ]
) -> tuple[FAQ | None, float]:
    tokens_pregunta = _tokenizar(pregunta, idioma)
    if not tokens_pregunta:
        return None, 0.0

    mejor: FAQ | None = None
    mejor_score = 0.0

    pregunta_attr, frases_attr, _ = _campos_idioma(idioma)

    for faq in faqs:
        # Incluye la pregunta canónica y las frases de entrenamiento del idioma
        candidatos: list[str] = []
        canonica = getattr(faq, pregunta_attr, None) or faq.pregunta_es
        if canonica:
            candidatos.append(canonica)
        frases = getattr(faq, frases_attr, None)
        if frases:
            candidatos.extend(frases)

        score_faq = 0.0
        for cand in candidatos:
            score = _similitud(tokens_pregunta, _tokenizar(cand, idioma))
            if score > score_faq:
                score_faq = score

        if score_faq > mejor_score:
            mejor_score = score_faq
            mejor = faq

    return mejor, mejor_score


def _respuesta_idioma(faq: FAQ, idioma: str) -> str:
    """Selecciona la respuesta en el idioma solicitado, con fallback a español."""
    candidato = getattr(faq, f"respuesta_{idioma}", None)
    if candidato:
        return candidato
    return faq.respuesta_es


def _fuera_de_dominio_msg(idioma: str) -> str:
    msgs = {
        "es": "No dispongo de información sobre esa consulta. ¿Puedo ayudarte con rutas, playas, eventos o servicios turísticos de Níjar?",
        "en": "I don't have information about that. Can I help you with routes, beaches, events, or tourist services in Níjar?",
        "de": "Dazu habe ich leider keine Informationen. Kann ich Ihnen bei Routen, Stränden, Veranstaltungen oder touristischen Dienstleistungen in Níjar helfen?",
        "fr": "Je ne dispose pas d'informations sur ce sujet. Puis-je vous aider avec les itinéraires, plages, événements ou services touristiques de Níjar ?",
    }
    return msgs.get(idioma, msgs["es"])


def _sugerencias_iniciales(idioma: str) -> list[str]:
    sug = {
        "es": [
            "¿Qué playas puedo visitar en Cabo de Gata?",
            "¿Cuál es el horario del Centro de Visitantes Las Amoladeras?",
            "¿Cómo llego a la ruta Rodalquilar–Albaricoques?",
        ],
        "en": [
            "Which beaches can I visit in Cabo de Gata?",
            "What are the opening hours of Las Amoladeras Visitor Center?",
            "How do I get to the Rodalquilar–Albaricoques route?",
        ],
        "de": [
            "Welche Strände kann ich in Cabo de Gata besuchen?",
            "Wie sind die Öffnungszeiten des Besucherzentrums Las Amoladeras?",
            "Wie komme ich zur Route Rodalquilar–Albaricoques?",
        ],
        "fr": [
            "Quelles plages puis-je visiter à Cabo de Gata ?",
            "Quels sont les horaires du Centre des Visiteurs Las Amoladeras ?",
            "Comment me rendre à l'itinéraire Rodalquilar–Albaricoques ?",
        ],
    }
    return sug.get(idioma, sug["es"])


# ----------------- API pública del servicio -----------------

async def consultar(
    db: AsyncSession, payload: ChatQueryIn
) -> ChatResponseOut:
    inicio = time.perf_counter()
    faqs = await _cargar_faqs_activas(db)

    mejor, score = _buscar_mejor_intent(payload.pregunta, payload.idioma, faqs)

    if mejor is None or score < UMBRAL_CONFIANZA_MEDIA:
        nivel = NivelConfianza.FUERA_DE_DOMINIO
        respuesta = _fuera_de_dominio_msg(payload.idioma)
        intent_detectado: str | None = None
        fuentes: list[FuenteRespuesta] | None = None
    elif score < UMBRAL_CONFIANZA_ALTA:
        nivel = NivelConfianza.MEDIA
        respuesta = _respuesta_idioma(mejor, payload.idioma)
        intent_detectado = mejor.intent
        fuentes = [
            FuenteRespuesta(
                tipo="faq",
                referencia=mejor.intent,
                descripcion=mejor.fuente_descripcion,
                fecha=str(mejor.updated_at.date()) if mejor.updated_at else None,
            )
        ]
    else:
        nivel = (
            NivelConfianza.ALTA
            if mejor.nivel_confianza == NivelConfianza.ALTA
            else NivelConfianza.MEDIA
        )
        respuesta = _respuesta_idioma(mejor, payload.idioma)
        intent_detectado = mejor.intent
        fuentes = [
            FuenteRespuesta(
                tipo="oficial" if nivel == NivelConfianza.ALTA else "dinamica",
                referencia=mejor.fuente_url or mejor.intent,
                descripcion=mejor.fuente_descripcion,
                fecha=str(mejor.updated_at.date()) if mejor.updated_at else None,
            )
        ]

    latencia_ms = int((time.perf_counter() - inicio) * 1000)

    interaccion = InteraccionChatbot(
        sesion_id=payload.sesion_id,
        canal=payload.canal,
        idioma=payload.idioma,
        pregunta=payload.pregunta,
        intent_detectado=intent_detectado,
        nivel_confianza=str(nivel.value if hasattr(nivel, "value") else nivel),
        score_confianza=round(float(score), 4),
        respuesta=respuesta,
        fuentes=[f.model_dump() for f in fuentes] if fuentes else None,
        latencia_ms=latencia_ms,
    )
    db.add(interaccion)
    await db.flush()
    await db.refresh(interaccion)

    sugerencias = (
        _sugerencias_iniciales(payload.idioma)
        if nivel == NivelConfianza.FUERA_DE_DOMINIO
        else None
    )

    return ChatResponseOut(
        interaccion_id=interaccion.id,
        respuesta=respuesta,
        intent_detectado=intent_detectado,
        nivel_confianza=str(nivel.value if hasattr(nivel, "value") else nivel),
        score_confianza=round(float(score), 4),
        fuentes=fuentes,
        sugerencias=sugerencias,
        latencia_ms=latencia_ms,
    )


async def registrar_feedback(
    db: AsyncSession, interaccion_id: UUID, util: bool, comentario: str | None
) -> None:
    obj = await db.get(InteraccionChatbot, interaccion_id)
    if obj is None:
        raise ValueError(f"Interacción {interaccion_id} no encontrada")
    obj.util = util
    obj.comentario = comentario
    await db.flush()


async def listar_intents(db: AsyncSession) -> list[IntentInfo]:
    res = await db.execute(
        select(FAQ).where(FAQ.activo.is_(True)).where(FAQ.deleted_at.is_(None)).order_by(FAQ.intent)
    )
    out: list[IntentInfo] = []
    for f in res.scalars().all():
        cobertura: list[str] = ["es"]
        if f.respuesta_en:
            cobertura.append("en")
        if f.respuesta_de:
            cobertura.append("de")
        if f.respuesta_fr:
            cobertura.append("fr")
        out.append(
            IntentInfo(
                intent=f.intent,
                categoria=f.categoria,
                pregunta_es=f.pregunta_es,
                nivel_confianza=str(
                    f.nivel_confianza.value
                    if hasattr(f.nivel_confianza, "value")
                    else f.nivel_confianza
                ),
                cobertura_idiomas=cobertura,
            )
        )
    return out


async def telemetria(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> ChatbotTelemetry:
    base = select(InteraccionChatbot)
    if desde:
        base = base.where(InteraccionChatbot.created_at >= desde)
    if hasta:
        base = base.where(InteraccionChatbot.created_at <= hasta)

    rows_res = await db.execute(base)
    interacciones = list(rows_res.scalars().all())

    total = len(interacciones)
    sesiones = {i.sesion_id for i in interacciones}
    resueltas = sum(1 for i in interacciones if i.nivel_confianza in {"alta", "media"})
    feedback_util = [i.util for i in interacciones if i.util is not None]

    idiomas = Counter(i.idioma for i in interacciones)
    idiomas_pct = (
        {k: round(v * 100 / total, 2) for k, v in idiomas.items()} if total else {}
    )

    intents = Counter(i.intent_detectado for i in interacciones if i.intent_detectado)
    top = [TopIntentItem(nombre=k, ocurrencias=v) for k, v in intents.most_common(10)]

    return ChatbotTelemetry(
        desde=desde,
        hasta=hasta,
        sesiones_totales=len(sesiones),
        sesiones_unicas=len(sesiones),
        interacciones_totales=total,
        resolucion_autonoma_porc=round(resueltas * 100 / total, 2) if total else 0.0,
        satisfaccion_porc=(
            round(sum(1 for u in feedback_util if u) * 100 / len(feedback_util), 2)
            if feedback_util
            else None
        ),
        idiomas_distribucion=idiomas_pct,
        top_intents=top,
    )


async def telemetria_series(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    granularidad: str = "dia",
) -> SerieDiaria:
    """Serie temporal diaria de interacciones del chatbot.

    Cuenta las filas de ``interacciones_chatbot`` agrupadas por día de
    creación para alimentar la gráfica de actividad del dashboard.
    """
    bucket = func.date_trunc("day", InteraccionChatbot.created_at).label("bucket")
    q = select(bucket, func.count().label("total"))
    if desde:
        q = q.where(InteraccionChatbot.created_at >= desde)
    if hasta:
        q = q.where(InteraccionChatbot.created_at <= hasta)
    q = q.group_by(bucket).order_by(bucket)

    rows = (await db.execute(q)).all()
    puntos = [
        PuntoSerieDiaria(fecha=row.bucket.date(), total=int(row.total)) for row in rows
    ]
    return SerieDiaria(granularidad=granularidad, desde=desde, hasta=hasta, puntos=puntos)
