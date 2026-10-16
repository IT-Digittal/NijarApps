"""Listados de interacciones de los visitantes: chatbot y contenidos del tótem.

- **Chatbot**: cada pregunta y respuesta del asistente (tabla
  ``interacciones_chatbot``), filtrable por canal, tótem, idioma, intención,
  nivel de confianza, valoración y texto libre.
- **Tótem**: lo que el visitante va viendo en el tótem (secciones, fichas,
  noticias, mapa, QR, idioma…). El tótem envía lotes de eventos al endpoint
  público ``POST /dashboards/totems/eventos``; cada evento se guarda como una
  ``Visita`` de tipo ``interaccion_totem`` con ``canal = "totem"``.

Los registros de demostración (semillas) se distinguen de los reales: en el
chatbot por la sesión ``demo-…`` y en el tótem por no venir del canal
``totem`` (las semillas usan ``totem_<nombre>``). Por defecto los listados
muestran solo los reales.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import String, and_, func, literal_column, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from nijar_dti.models.faq import InteraccionChatbot
from nijar_dti.models.visita import TipoVisita, Visita
from nijar_dti.schemas.interacciones import (
    ContenidoTop,
    EventosTotemIn,
    InteraccionChatbotOut,
    InteraccionTotemOut,
    ListadoChatbot,
    ListadoTotem,
    ResumenListadoChatbot,
    ResumenListadoTotem,
)

CANAL_TOTEM = "totem"
# Acciones que cuentan como «ver» un contenido (para el ranking de más vistos)
EVENTOS_DE_CONTENIDO = ("ficha", "noticia", "mapa_punto")
MAX_EXPORTACION = 50_000

# Sesión del tótem: «totem-urn:ngsi-ld:Totem:nijar:<tótem>-<marca de tiempo>»
_RE_SESION_TOTEM = re.compile(r"^totem-.*?:([a-z0-9_-]+)-\d+$")
_RE_SLUG = re.compile(r"^[a-z0-9_-]{1,40}$")


def totem_de_sesion(sesion_id: str | None) -> str | None:
    """Nombre corto del tótem a partir del identificador de sesión del chatbot."""
    m = _RE_SESION_TOTEM.match(sesion_id or "")
    return m.group(1) if m else None


def _like(texto: str) -> str:
    """Patrón ILIKE con los comodines del usuario escapados."""
    esc = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{esc}%"


def _hasta_inclusivo(hasta: datetime | None) -> datetime | None:
    """Una fecha sin hora («2026-10-16») incluye todo ese día."""
    if hasta is not None and (hasta.hour, hasta.minute, hasta.second) == (0, 0, 0):
        return hasta + timedelta(days=1) - timedelta(microseconds=1)
    return hasta


# =============================== Chatbot ===============================


def _filtros_chatbot(
    *,
    desde: datetime | None,
    hasta: datetime | None,
    canal: str | None,
    totem: str | None,
    idioma: str | None,
    intent: str | None,
    nivel: str | None,
    util: str | None,
    q: str | None,
    sesion: str | None,
    incluir_demo: bool,
) -> list[ColumnElement[bool]]:
    m = InteraccionChatbot
    f: list[ColumnElement[bool]] = [m.deleted_at.is_(None)]
    if not incluir_demo:
        f.append(not_(m.sesion_id.like("demo-%")))
    if desde:
        f.append(m.created_at >= desde)
    if (h := _hasta_inclusivo(hasta)) is not None:
        f.append(m.created_at <= h)
    if canal:
        f.append(m.canal == canal)
    if totem and _RE_SLUG.match(totem):
        f.append(m.sesion_id.like(f"totem-%:{totem}-%"))
    if idioma:
        f.append(m.idioma == idioma)
    if intent == "(sin intención)":
        f.append(m.intent_detectado.is_(None))
    elif intent:
        f.append(m.intent_detectado == intent)
    if nivel:
        f.append(m.nivel_confianza == nivel)
    if util == "si":
        f.append(m.util.is_(True))
    elif util == "no":
        f.append(m.util.is_(False))
    elif util == "sin":
        f.append(m.util.is_(None))
    if sesion:
        f.append(m.sesion_id == sesion)
    if q and q.strip():
        patron = _like(q.strip())
        f.append(
            or_(
                m.pregunta.ilike(patron, escape="\\"),
                m.respuesta.ilike(patron, escape="\\"),
                m.intent_detectado.ilike(patron, escape="\\"),
            )
        )
    return f


def _chatbot_out(r: InteraccionChatbot) -> InteraccionChatbotOut:
    return InteraccionChatbotOut(
        id=r.id,
        fecha=r.created_at,
        canal=r.canal,
        totem=totem_de_sesion(r.sesion_id),
        sesion_id=r.sesion_id,
        idioma=r.idioma,
        pregunta=r.pregunta,
        respuesta=r.respuesta,
        intent_detectado=r.intent_detectado,
        nivel_confianza=r.nivel_confianza,
        score_confianza=r.score_confianza,
        util=r.util,
        comentario=r.comentario,
        latencia_ms=r.latencia_ms,
        fuentes=r.fuentes,
        demo=r.sesion_id.startswith("demo-"),
    )


_ORDEN_CHATBOT: dict[str, ColumnElement[Any]] = {
    "reciente": InteraccionChatbot.created_at.desc(),
    "antiguo": InteraccionChatbot.created_at.asc(),
    "latencia": InteraccionChatbot.latencia_ms.desc().nulls_last(),
    "confianza": InteraccionChatbot.score_confianza.asc().nulls_first(),
}


async def _facetas(
    db: AsyncSession, columnas: dict[str, Any], filtros: Sequence[ColumnElement[bool]], modelo: Any
) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for nombre, col in columnas.items():
        filas = (
            await db.execute(
                select(col, func.count()).select_from(modelo).where(*filtros).group_by(col)
            )
        ).all()
        out[nombre] = {
            (str(v) if v is not None else "(sin intención)" if nombre == "intent" else "—"): int(n)
            for v, n in sorted(filas, key=lambda x: -x[1])
        }
    return out


async def listar_chatbot(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    orden: str = "reciente",
    **filtros: Any,
) -> ListadoChatbot:
    m = InteraccionChatbot
    f = _filtros_chatbot(**filtros)
    total = int((await db.execute(select(func.count()).select_from(m).where(*f))).scalar_one())
    filas = (
        (
            await db.execute(
                select(m)
                .where(*f)
                .order_by(_ORDEN_CHATBOT.get(orden, _ORDEN_CHATBOT["reciente"]))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    agg = (
        await db.execute(
            select(
                func.count(func.distinct(m.sesion_id)),
                func.count().filter(m.nivel_confianza == "fuera_de_dominio"),
                func.count().filter(m.util.is_(True)),
                func.count().filter(m.util.is_(False)),
                func.avg(m.latencia_ms),
            ).where(*f)
        )
    ).one()
    # Facetas: valores disponibles con el periodo y el origen elegidos (sin el resto de filtros)
    base = _filtros_chatbot(
        desde=filtros.get("desde"),
        hasta=filtros.get("hasta"),
        canal=None,
        totem=None,
        idioma=None,
        intent=None,
        nivel=None,
        util=None,
        q=None,
        sesion=None,
        incluir_demo=bool(filtros.get("incluir_demo")),
    )
    facetas = await _facetas(
        db,
        {"canal": m.canal, "idioma": m.idioma, "intent": m.intent_detectado},
        base,
        m,
    )
    sesiones_totem = (
        await db.execute(
            select(m.sesion_id).where(*base, m.canal == CANAL_TOTEM).distinct().limit(5000)
        )
    ).scalars()
    totems: dict[str, int] = {}
    for s in sesiones_totem:
        if t := totem_de_sesion(s):
            totems[t] = totems.get(t, 0) + 1
    facetas["totem"] = totems
    return ListadoChatbot(
        items=[_chatbot_out(r) for r in filas],
        total=total,
        page=page,
        page_size=page_size,
        resumen=ResumenListadoChatbot(
            interacciones=total,
            sesiones=int(agg[0] or 0),
            sin_respuesta=int(agg[1] or 0),
            utiles=int(agg[2] or 0),
            no_utiles=int(agg[3] or 0),
            latencia_media_ms=round(float(agg[4]), 1) if agg[4] is not None else None,
        ),
        facetas=facetas,
    )


async def exportar_chatbot(db: AsyncSession, orden: str = "reciente", **filtros: Any) -> list[dict]:
    m = InteraccionChatbot
    filas = (
        (
            await db.execute(
                select(m)
                .where(*_filtros_chatbot(**filtros))
                .order_by(_ORDEN_CHATBOT.get(orden, _ORDEN_CHATBOT["reciente"]))
                .limit(MAX_EXPORTACION)
            )
        )
        .scalars()
        .all()
    )
    out = []
    for r in filas:
        i = _chatbot_out(r)
        out.append(
            {
                "fecha": i.fecha.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "canal": i.canal,
                "totem": i.totem or "",
                "sesion": i.sesion_id,
                "idioma": i.idioma,
                "pregunta": i.pregunta,
                "respuesta": i.respuesta,
                "intencion": i.intent_detectado or "",
                "confianza": i.nivel_confianza,
                "puntuacion": "" if i.score_confianza is None else round(i.score_confianza, 3),
                "util": {True: "sí", False: "no", None: ""}[i.util],
                "comentario": i.comentario or "",
                "latencia_ms": "" if i.latencia_ms is None else i.latencia_ms,
                "demo": "sí" if i.demo else "",
            }
        )
    return out


async def conversacion(db: AsyncSession, sesion_id: str) -> list[InteraccionChatbotOut]:
    m = InteraccionChatbot
    filas = (
        (
            await db.execute(
                select(m)
                .where(m.sesion_id == sesion_id, m.deleted_at.is_(None))
                .order_by(m.created_at.asc())
                .limit(500)
            )
        )
        .scalars()
        .all()
    )
    return [_chatbot_out(r) for r in filas]


# =============================== Tótem ===============================


_CLAVES_ATRIBUTOS = {
    "evento",
    "seccion",
    "contenido",
    "contenido_id",
    "detalle",
    "totem",
    "sesion",
    "duracion_seg",
}


def _attr(clave: str) -> ColumnElement[str]:
    """``atributos ->> 'clave'`` con la clave literal (no como parámetro): así
    PostgreSQL reconoce la misma expresión en el SELECT y en el GROUP BY."""
    if clave not in _CLAVES_ATRIBUTOS:
        raise ValueError(clave)
    return literal_column(f"(visitas.atributos ->> '{clave}')", String)


def _hash_sesion(sesion_id: str) -> str:
    return hashlib.sha256(f"totem-sesion:{sesion_id}".encode()).hexdigest()


async def registrar_eventos_totem(db: AsyncSession, lote: EventosTotemIn) -> int:
    """Guarda un lote de eventos del tótem. Devuelve cuántos se han guardado."""
    ahora = datetime.now(UTC)
    minimo = ahora - timedelta(hours=24)
    visitante = _hash_sesion(lote.sesion_id)
    for i, e in enumerate(lote.eventos):
        ts = e.ts
        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        if ts is None or not (minimo <= ts <= ahora + timedelta(minutes=5)):
            # Sin hora o reloj del tótem desajustado: hora del servidor (conservando el orden)
            ts = ahora + timedelta(microseconds=i)
        atributos: dict[str, Any] = {
            "origen": CANAL_TOTEM,
            "totem": lote.totem,
            "sesion": lote.sesion_id,
            "evento": e.evento,
        }
        for clave in ("seccion", "contenido_id", "contenido", "detalle", "duracion_seg"):
            valor = getattr(e, clave)
            if valor not in (None, ""):
                atributos[clave] = valor
        db.add(
            Visita(
                tipo=TipoVisita.INTERACCION_TOTEM,
                ocurrido_en=ts,
                visitante_hash=visitante,
                idioma=lote.idioma,
                canal=CANAL_TOTEM,
                atributos=atributos,
            )
        )
    await db.flush()
    return len(lote.eventos)


def _filtros_totem(
    *,
    desde: datetime | None,
    hasta: datetime | None,
    totem: str | None,
    evento: str | None,
    seccion: str | None,
    idioma: str | None,
    q: str | None,
    sesion: str | None,
    incluir_demo: bool,
) -> list[ColumnElement[bool]]:
    f: list[ColumnElement[bool]] = [Visita.tipo == TipoVisita.INTERACCION_TOTEM]
    if not incluir_demo:
        f.append(Visita.canal == CANAL_TOTEM)
    if desde:
        f.append(Visita.ocurrido_en >= desde)
    if (h := _hasta_inclusivo(hasta)) is not None:
        f.append(Visita.ocurrido_en <= h)
    if totem:
        f.append(
            or_(
                and_(Visita.canal == CANAL_TOTEM, _attr("totem") == totem),
                Visita.canal == f"totem_{totem}",
            )
        )
    if evento:
        f.append(_attr("evento") == evento)
    if seccion:
        f.append(_attr("seccion") == seccion)
    if idioma:
        f.append(Visita.idioma == idioma)
    if sesion:
        f.append(_attr("sesion") == sesion)
    if q and q.strip():
        patron = _like(q.strip())
        f.append(
            or_(
                _attr("contenido").ilike(patron, escape="\\"),
                _attr("detalle").ilike(patron, escape="\\"),
                _attr("seccion").ilike(patron, escape="\\"),
            )
        )
    return f


def _totem_out(v: Visita) -> InteraccionTotemOut:
    a = v.atributos or {}
    real = v.canal == CANAL_TOTEM
    dur = a.get("duracion_seg")
    return InteraccionTotemOut(
        id=v.id,
        fecha=v.ocurrido_en,
        totem=a.get("totem") if real else (v.canal or "").removeprefix("totem_") or None,
        sesion=a.get("sesion"),
        evento=a.get("evento") if real else "interaccion",
        seccion=a.get("seccion"),
        contenido=a.get("contenido"),
        contenido_id=a.get("contenido_id"),
        detalle=a.get("detalle"),
        idioma=v.idioma,
        duracion_seg=float(dur) if isinstance(dur, (int, float)) else None,
        demo=not real,
    )


_ORDEN_TOTEM: dict[str, ColumnElement[Any]] = {
    "reciente": Visita.ocurrido_en.desc(),
    "antiguo": Visita.ocurrido_en.asc(),
}


async def listar_totem(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    orden: str = "reciente",
    **filtros: Any,
) -> ListadoTotem:
    f = _filtros_totem(**filtros)
    total = int((await db.execute(select(func.count()).select_from(Visita).where(*f))).scalar_one())
    filas = (
        (
            await db.execute(
                select(Visita)
                .where(*f)
                .order_by(_ORDEN_TOTEM.get(orden, _ORDEN_TOTEM["reciente"]))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    sesiones = int(
        (
            await db.execute(select(func.count(func.distinct(Visita.visitante_hash))).where(*f))
        ).scalar_one()
        or 0
    )
    duraciones = (
        await db.execute(
            select(_attr("duracion_seg")).where(*f, _attr("duracion_seg").isnot(None)).limit(20000)
        )
    ).scalars()
    valores = [float(d) for d in duraciones if d not in (None, "")]
    contenido = _attr("contenido")
    top = (
        await db.execute(
            select(contenido, _attr("seccion"), func.count())
            .where(*f, contenido.isnot(None), _attr("evento").in_(EVENTOS_DE_CONTENIDO))
            .group_by(contenido, _attr("seccion"))
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()
    base = _filtros_totem(
        desde=filtros.get("desde"),
        hasta=filtros.get("hasta"),
        totem=None,
        evento=None,
        seccion=None,
        idioma=None,
        q=None,
        sesion=None,
        incluir_demo=bool(filtros.get("incluir_demo")),
    )
    facetas = await _facetas(
        db,
        {"evento": _attr("evento"), "seccion": _attr("seccion"), "idioma": Visita.idioma},
        base,
        Visita,
    )
    totems = (
        await db.execute(
            select(Visita.canal, _attr("totem"), func.count())
            .where(*base)
            .group_by(Visita.canal, _attr("totem"))
        )
    ).all()
    por_totem: dict[str, int] = {}
    for canal_v, t, n in totems:
        nombre = t if canal_v == CANAL_TOTEM else (canal_v or "").removeprefix("totem_")
        if nombre:
            por_totem[nombre] = por_totem.get(nombre, 0) + int(n)
    facetas["totem"] = por_totem
    facetas.get("evento", {}).pop("—", None)
    return ListadoTotem(
        items=[_totem_out(v) for v in filas],
        total=total,
        page=page,
        page_size=page_size,
        resumen=ResumenListadoTotem(
            interacciones=total,
            sesiones=sesiones,
            duracion_media_seg=round(sum(valores) / len(valores), 1) if valores else None,
            contenidos_top=[ContenidoTop(contenido=c, seccion=s, vistas=int(n)) for c, s, n in top],
        ),
        facetas=facetas,
    )


async def exportar_totem(db: AsyncSession, orden: str = "reciente", **filtros: Any) -> list[dict]:
    filas = (
        (
            await db.execute(
                select(Visita)
                .where(*_filtros_totem(**filtros))
                .order_by(_ORDEN_TOTEM.get(orden, _ORDEN_TOTEM["reciente"]))
                .limit(MAX_EXPORTACION)
            )
        )
        .scalars()
        .all()
    )
    out = []
    for v in filas:
        i = _totem_out(v)
        out.append(
            {
                "fecha": i.fecha.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "totem": i.totem or "",
                "sesion": i.sesion or "",
                "evento": i.evento or "",
                "seccion": i.seccion or "",
                "contenido": i.contenido or "",
                "detalle": i.detalle or "",
                "idioma": i.idioma or "",
                "duracion_seg": "" if i.duracion_seg is None else i.duracion_seg,
                "demo": "sí" if i.demo else "",
            }
        )
    return out


async def recorrido_sesion(db: AsyncSession, sesion: str) -> list[InteraccionTotemOut]:
    filas = (
        (
            await db.execute(
                select(Visita)
                .where(
                    Visita.tipo == TipoVisita.INTERACCION_TOTEM,
                    Visita.canal == CANAL_TOTEM,
                    _attr("sesion") == sesion,
                )
                .order_by(Visita.ocurrido_en.asc())
                .limit(1000)
            )
        )
        .scalars()
        .all()
    )
    return [_totem_out(v) for v in filas]
