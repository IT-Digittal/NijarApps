"""Traducción automática de contenidos del tótem (avisos, noticias, agenda).

Los avisos del CMS y las noticias de la web municipal (Strapi) llegan solo en
español. Cuando el tótem los pide en inglés, alemán o francés se traducen con
el modelo de OpenAI configurado (``OPENAI_API_KEY`` / ``OPENAI_MODEL``, los
mismos del chatbot) y el resultado se guarda en la tabla ``traducciones``:
cada texto se traduce una sola vez por idioma.

Solo se traducen contenidos propios de la plataforma (no hay un endpoint
público de «traducir texto libre»), así que el gasto queda acotado. Cada
llamada se registra en el control de consumo de IA (servicio ``traduccion``).

Si no hay clave de OpenAI o la llamada falla, se devuelve el texto original:
el tótem nunca se queda sin contenido por un fallo de traducción.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import Sequence
from contextlib import suppress
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import Settings, get_settings
from nijar_dti.core.logging import get_logger
from nijar_dti.models.traduccion import Traduccion
from nijar_dti.schemas.cms import AvisoPublicoOut
from nijar_dti.schemas.common import I18nText
from nijar_dti.schemas.noticias import NoticiaOut
from nijar_dti.schemas.tourism import EventoTuristicoOut

logger = get_logger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
IDIOMA_ORIGEN = "es"
IDIOMAS_DESTINO = {"en": "inglés", "de": "alemán", "fr": "francés"}
# Tamaño de cada lote enviado al modelo (caracteres de texto de origen)
MAX_CARACTERES_LOTE = 6000
MAX_TOKENS_SALIDA = 4000

_INSTRUCCIONES = (
    "Eres el traductor oficial de la web turística del Ayuntamiento de Níjar "
    "(Almería, Parque Natural Cabo de Gata-Níjar). Traduce del español al {idioma} "
    "cada elemento de la lista que recibes, con un tono informativo y cercano. "
    "Reglas: conserva intactas las etiquetas HTML, los atributos, las URLs, los "
    "números, las fechas y los teléfonos; no traduzcas los nombres propios de "
    "lugares (Níjar, Cabo de Gata, Rodalquilar, San José, Las Negras…) ni de "
    "personas o entidades; no añadas ni quites información. Responde SOLO con un "
    'JSON {{"t": [...]}} con las traducciones en el mismo orden y número de elementos.'
)


class TraduccionError(Exception):
    """El proveedor de IA no devolvió una traducción válida."""


def traduccion_disponible(settings: Settings | None = None) -> bool:
    return bool((settings or get_settings()).openai_api_key)


def _clave(idioma: str, texto: str) -> str:
    return hashlib.sha256(f"{idioma}\x00{texto}".encode()).hexdigest()


def _lotes(textos: Sequence[str]) -> list[list[str]]:
    lotes: list[list[str]] = []
    actual: list[str] = []
    tam = 0
    for t in textos:
        if actual and tam + len(t) > MAX_CARACTERES_LOTE:
            lotes.append(actual)
            actual, tam = [], 0
        actual.append(t)
        tam += len(t)
    if actual:
        lotes.append(actual)
    return lotes


async def _llamar_modelo(
    settings: Settings, idioma: str, textos: list[str]
) -> tuple[list[str], dict]:
    """Traduce un lote con Chat Completions (modo JSON). Devuelve (traducciones, uso)."""
    sistema = _INSTRUCCIONES.format(idioma=IDIOMAS_DESTINO[idioma])
    async with httpx.AsyncClient(timeout=max(settings.openai_timeout_seconds, 30)) as client:
        resp = await client.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": json.dumps({"t": textos}, ensure_ascii=False)},
                ],
                "temperature": 0.2,
                "max_tokens": MAX_TOKENS_SALIDA,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
    contenido = data["choices"][0]["message"]["content"] or "{}"
    try:
        salida = json.loads(contenido).get("t")
    except (json.JSONDecodeError, AttributeError) as exc:
        raise TraduccionError("Respuesta del modelo no es JSON") from exc
    if not isinstance(salida, list) or len(salida) != len(textos):
        raise TraduccionError("El modelo no devolvió una traducción por texto")
    return [str(x) for x in salida], data.get("usage") or {}


async def traducir(
    db: AsyncSession,
    textos: Sequence[str | None],
    idioma: str,
    *,
    canal: str = "totem",
    settings: Settings | None = None,
) -> list[str | None]:
    """Devuelve los textos traducidos a ``idioma`` (mismo orden; None se mantiene).

    Usa la caché y solo envía al modelo lo que falta. Ante cualquier fallo
    devuelve el texto original.
    """
    settings = settings or get_settings()
    salida: list[str | None] = list(textos)
    if idioma not in IDIOMAS_DESTINO:
        return salida
    unicos = sorted({t for t in textos if t and t.strip()})
    if not unicos:
        return salida

    claves = {t: _clave(idioma, t) for t in unicos}
    filas = await db.execute(
        select(Traduccion.clave, Traduccion.texto_traducido).where(
            Traduccion.clave.in_(list(claves.values()))
        )
    )
    cache: dict[str, str] = {fila[0]: fila[1] for fila in filas.all()}
    hechas = {t: cache[k] for t, k in claves.items() if k in cache}
    pendientes = [t for t in unicos if t not in hechas]

    if pendientes and traduccion_disponible(settings):
        for lote in _lotes(pendientes):
            inicio = time.perf_counter()
            try:
                traducidos, uso = await _llamar_modelo(settings, idioma, lote)
            except (httpx.HTTPError, TraduccionError, KeyError) as exc:
                logger.warning(
                    "traduccion_fallida", idioma=idioma, textos=len(lote), error=str(exc)
                )
                continue
            filas_nuevas = [
                {
                    "id": uuid4(),
                    "clave": claves[o],
                    "idioma": idioma,
                    "texto_origen": o,
                    "texto_traducido": tr,
                    "modelo": settings.openai_model,
                }
                for o, tr in zip(lote, traducidos, strict=True)
            ]
            # Varios workers pueden traducir lo mismo a la vez: gana el primero
            await db.execute(
                insert(Traduccion)
                .values(filas_nuevas)
                .on_conflict_do_nothing(index_elements=["clave"])
            )
            hechas.update(zip(lote, traducidos, strict=True))
            await _registrar_consumo(db, settings, idioma, canal, uso, inicio)
        await db.commit()

    return [hechas.get(t, t) if t else t for t in textos]


async def _registrar_consumo(
    db: AsyncSession, settings: Settings, idioma: str, canal: str, uso: dict, inicio: float
) -> None:
    from nijar_dti.services import consumo_ia_service

    try:
        await consumo_ia_service.registrar(
            db,
            modelo=settings.openai_model,
            servicio="traduccion",
            canal=canal,
            idioma=idioma,
            tokens_entrada=int(uso.get("prompt_tokens") or 0),
            tokens_salida=int(uso.get("completion_tokens") or 0),
            latencia_ms=int((time.perf_counter() - inicio) * 1000),
        )
    except Exception:  # noqa: BLE001 — el registro de costes nunca rompe la traducción
        logger.warning("No se pudo registrar el consumo de IA de la traducción", exc_info=True)


# ---------------------------------------------------------------------------
# Aplicación a los contenidos que consume el tótem
# ---------------------------------------------------------------------------


def _hace_falta(idioma: str | None) -> bool:
    return idioma in IDIOMAS_DESTINO


def _con_idioma(
    i18n: I18nText | None, base: str | None, idioma: str, valor: str | None
) -> I18nText:
    """Copia de ``i18n`` con el idioma pedido relleno (y el español, si faltaba)."""
    datos = i18n.model_dump() if i18n else {}
    datos.setdefault("es", None)
    datos["es"] = datos["es"] or base
    datos[idioma] = valor
    return I18nText(**datos)


def _falta(i18n: I18nText | None, idioma: str) -> bool:
    return not (i18n and getattr(i18n, idioma, None))


async def traducir_avisos(
    db: AsyncSession, avisos: list[AvisoPublicoOut], idioma: str | None
) -> list[AvisoPublicoOut]:
    """Rellena ``titulo_i18n``/``cuerpo_i18n`` en el idioma pedido si el CMS no lo trae."""
    if not _hace_falta(idioma) or not avisos:
        return avisos
    assert idioma is not None
    textos: list[str | None] = []
    for a in avisos:
        textos.append(a.titulo if _falta(a.titulo_i18n, idioma) else None)
        textos.append(a.cuerpo if _falta(a.cuerpo_i18n, idioma) else None)
    tr = await traducir(db, textos, idioma)
    out = []
    for i, a in enumerate(avisos):
        cambios: dict = {}
        if textos[2 * i]:
            cambios["titulo_i18n"] = _con_idioma(a.titulo_i18n, a.titulo, idioma, tr[2 * i])
        if textos[2 * i + 1]:
            cambios["cuerpo_i18n"] = _con_idioma(a.cuerpo_i18n, a.cuerpo, idioma, tr[2 * i + 1])
        out.append(a.model_copy(update=cambios) if cambios else a)
    return out


async def traducir_noticias(
    db: AsyncSession, noticias: list[NoticiaOut], idioma: str | None
) -> list[NoticiaOut]:
    """Traduce título, resumen y (en el detalle) el contenido HTML de las noticias.

    Devuelve copias: los listados en memoria del servicio de noticias no se tocan.
    """
    if not _hace_falta(idioma) or not noticias:
        return noticias
    assert idioma is not None
    campos = ("titulo", "descripcion", "contenido")
    textos: list[str | None] = [getattr(n, c) for n in noticias for c in campos]
    tr = await traducir(db, textos, idioma)
    out = []
    for i, n in enumerate(noticias):
        base = i * len(campos)
        out.append(n.model_copy(update={c: tr[base + j] for j, c in enumerate(campos)}))
    return out


async def traducir_eventos(
    db: AsyncSession, eventos: list[EventoTuristicoOut], idioma: str | None
) -> list[EventoTuristicoOut]:
    """Completa nombre y descripción de los eventos sin traducción y traduce el precio."""
    if not _hace_falta(idioma) or not eventos:
        return eventos
    assert idioma is not None
    textos: list[str | None] = []
    for e in eventos:
        textos.append(e.nombre if _falta(e.nombre_i18n, idioma) else None)
        textos.append(
            e.descripcion if e.descripcion and _falta(e.descripcion_i18n, idioma) else None
        )
        textos.append(e.precio)
    tr = await traducir(db, textos, idioma)
    out = []
    for i, e in enumerate(eventos):
        nombre, desc, precio = tr[3 * i], tr[3 * i + 1], tr[3 * i + 2]
        cambios: dict = {"precio": precio}
        if textos[3 * i]:
            cambios["nombre_i18n"] = _con_idioma(e.nombre_i18n, e.nombre, idioma, nombre)
        if textos[3 * i + 1]:
            cambios["descripcion_i18n"] = _con_idioma(
                e.descripcion_i18n, e.descripcion, idioma, desc
            )
        out.append(e.model_copy(update=cambios))
    return out


async def precalentar_traducciones_loop(interval_seconds: int) -> None:
    """Deja traducido de antemano lo que el tótem muestra (sin esperas al visitante).

    En cada vuelta: avisos publicados, eventos próximos, últimas noticias y
    agenda cultural (con el contenido completo de las más recientes). Lo ya
    traducido sale de la caché, así que solo se paga lo nuevo.
    """
    from datetime import UTC, datetime

    from nijar_dti.connectors.noticias import NoticiasError
    from nijar_dti.core.database import AsyncSessionLocal
    from nijar_dti.schemas.common import PageParams
    from nijar_dti.schemas.tourism import EventoFilter
    from nijar_dti.services import cms_service, noticias_service, tourism_service

    while True:
        if traduccion_disponible():
            try:
                async with AsyncSessionLocal() as db:
                    avisos = [
                        AvisoPublicoOut.model_validate(c)
                        for c in await cms_service.contenidos_publicos_canal(db, "totem")
                    ]
                    filas, _ = await tourism_service.listar_eventos(
                        db,
                        EventoFilter(desde=datetime.now(UTC), publicado=True),
                        PageParams(page=1, page_size=50),
                    )
                    eventos = [await tourism_service.evento_to_out(db, e) for e in filas]
                    noticias: list[NoticiaOut] = []
                    listados = (noticias_service.listar_todas, noticias_service.listar_agenda)
                    if noticias_service.noticias_configurado():
                        for listar in listados:
                            try:
                                pagina = await listar(page=1, page_size=12)
                            except NoticiasError:
                                continue
                            noticias.extend(pagina.items)
                            for n in pagina.items[:6]:
                                with suppress(NoticiasError):
                                    detalle = await noticias_service.noticia_por_slug(n.slug)
                                    if detalle:
                                        noticias.append(detalle)
                    for idioma in IDIOMAS_DESTINO:
                        await traducir_avisos(db, avisos, idioma)
                        await traducir_eventos(db, eventos, idioma)
                        await traducir_noticias(db, noticias, idioma)
                logger.info(
                    "traducciones_precalentadas",
                    avisos=len(avisos),
                    eventos=len(eventos),
                    noticias=len(noticias),
                )
            except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
                logger.error("Error precalentando traducciones", error=str(exc))
        await asyncio.sleep(interval_seconds)
