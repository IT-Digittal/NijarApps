"""Lógica de negocio del CMS centralizado (publicación multicanal)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.contenido import Contenido, EstadoContenido
from nijar_dti.schemas.cms import CANALES_VALIDOS, ContenidoIn
from nijar_dti.schemas.common import PageParams


class CMSError(Exception):
    pass


class CMSNotFound(CMSError):
    pass


class CMSValidation(CMSError):
    pass


def _validar_canales(canales: list[str]) -> None:
    invalidos = [c for c in canales if c not in CANALES_VALIDOS]
    if invalidos:
        raise CMSValidation(f"Canales no soportados: {invalidos}")


def _calcular_estado(payload: ContenidoIn, ahora: datetime) -> EstadoContenido:
    if not payload.publicar:
        return EstadoContenido.BORRADOR
    if payload.publicar_desde and payload.publicar_desde > ahora:
        return EstadoContenido.PROGRAMADO
    return EstadoContenido.PUBLICADO


async def crear_contenido(
    db: AsyncSession, payload: ContenidoIn, created_by: UUID | None = None
) -> Contenido:
    _validar_canales(payload.canales)
    ahora = datetime.now(UTC)
    obj = Contenido(
        titulo=payload.titulo,
        titulo_i18n=payload.titulo_i18n.model_dump(exclude_none=True)
        if payload.titulo_i18n
        else None,
        cuerpo=payload.cuerpo,
        cuerpo_i18n=payload.cuerpo_i18n.model_dump(exclude_none=True)
        if payload.cuerpo_i18n
        else None,
        canales=list(payload.canales),
        plantilla_id=payload.plantilla_id,
        recurso_id=payload.recurso_id,
        estado=_calcular_estado(payload, ahora),
        publicar_desde=payload.publicar_desde,
        publicar_hasta=payload.publicar_hasta,
        imagenes=payload.imagenes,
        enlaces=payload.enlaces,
        etiquetas=payload.etiquetas,
        metadata_adicional=None,
    )
    obj.created_by = created_by
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def listar_contenidos(
    db: AsyncSession,
    canal: str | None,
    idioma: str | None,
    page: PageParams,
) -> tuple[list[Contenido], int]:
    base = select(Contenido).where(Contenido.deleted_at.is_(None))
    if canal and canal != "todos":
        base = base.where(Contenido.canales.any(canal))
    if idioma:
        # filtra contenidos cuyo i18n.<idioma> está presente
        base = base.where(Contenido.titulo_i18n.op("?")(idioma) | (idioma == "es"))

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )
    res = await db.execute(
        base.order_by(Contenido.created_at.desc()).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


async def contenidos_publicos_canal(
    db: AsyncSession, canal: str, limite: int = 20
) -> list[Contenido]:
    """Contenidos visibles AHORA en un canal público (tótem, web, app).

    Los consume el tótem sin autenticación: publicados (o programados cuya
    ventana ya ha llegado) y dentro de ``publicar_desde``/``publicar_hasta``.
    """
    ahora = datetime.now(UTC)
    q = (
        select(Contenido)
        .where(
            Contenido.deleted_at.is_(None),
            Contenido.canales.any(canal),  # type: ignore[arg-type]
            Contenido.estado.in_([EstadoContenido.PUBLICADO, EstadoContenido.PROGRAMADO]),
            or_(Contenido.publicar_desde.is_(None), Contenido.publicar_desde <= ahora),
            or_(Contenido.publicar_hasta.is_(None), Contenido.publicar_hasta >= ahora),
        )
        .order_by(Contenido.created_at.desc())
        .limit(limite)
    )
    return list((await db.execute(q)).scalars().all())


async def obtener_contenido(db: AsyncSession, content_id: UUID) -> Contenido:
    obj = await db.get(Contenido, content_id)
    if obj is None or obj.deleted_at is not None:
        raise CMSNotFound(f"Contenido {content_id} no encontrado")
    return obj


async def actualizar_contenido(
    db: AsyncSession,
    content_id: UUID,
    payload: ContenidoIn,
    updated_by: UUID | None = None,
) -> Contenido:
    _validar_canales(payload.canales)
    obj = await obtener_contenido(db, content_id)
    ahora = datetime.now(UTC)
    obj.titulo = payload.titulo
    obj.titulo_i18n = (
        payload.titulo_i18n.model_dump(exclude_none=True) if payload.titulo_i18n else None
    )
    obj.cuerpo = payload.cuerpo
    obj.cuerpo_i18n = (
        payload.cuerpo_i18n.model_dump(exclude_none=True) if payload.cuerpo_i18n else None
    )
    obj.canales = list(payload.canales)
    obj.plantilla_id = payload.plantilla_id
    obj.recurso_id = payload.recurso_id
    obj.estado = _calcular_estado(payload, ahora)
    obj.publicar_desde = payload.publicar_desde
    obj.publicar_hasta = payload.publicar_hasta
    obj.imagenes = payload.imagenes
    obj.enlaces = payload.enlaces
    obj.etiquetas = payload.etiquetas
    obj.updated_by = updated_by
    await db.flush()
    await db.refresh(obj)
    return obj


async def despublicar_contenido(
    db: AsyncSession, content_id: UUID, updated_by: UUID | None = None
) -> None:
    obj = await obtener_contenido(db, content_id)
    obj.estado = EstadoContenido.ARCHIVADO
    obj.updated_by = updated_by
    obj.deleted_at = datetime.now(UTC)
    await db.flush()


PLANTILLAS_DISPONIBLES: list[dict] = [
    {"id": "tpl_basico", "nombre": "Plantilla básica", "descripcion": "Título + cuerpo + imagen"},
    {
        "id": "tpl_evento",
        "nombre": "Plantilla evento",
        "descripcion": "Evento con fecha y ubicación",
    },
    {"id": "tpl_ruta", "nombre": "Plantilla ruta", "descripcion": "Ruta con mapa y dificultad"},
    {
        "id": "tpl_alerta",
        "nombre": "Plantilla alerta",
        "descripcion": "Aviso urgente a pantalla completa",
    },
    {"id": "tpl_galeria", "nombre": "Plantilla galería", "descripcion": "Galería de imágenes"},
]


def listar_plantillas() -> list[dict]:
    return list(PLANTILLAS_DISPONIBLES)
