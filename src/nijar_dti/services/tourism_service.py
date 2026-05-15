"""Lógica de negocio para recursos turísticos, eventos y servicios.

Las funciones devuelven los objetos ORM en bruto. La conversión a los
esquemas de salida (con la geometría serializada como GeoJSON) la realiza
el helper `_to_geopoint` invocado por los endpoints.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_AsGeoJSON, ST_DWithin, ST_GeogFromText
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.servicio import Servicio
from nijar_dti.schemas.common import GeoPoint, PageParams
from nijar_dti.schemas.tourism import (
    EventoFilter,
    EventoTuristicoIn,
    EventoTuristicoOut,
    RecursoTuristicoFilter,
    RecursoTuristicoIn,
    RecursoTuristicoOut,
    ServicioFilter,
    ServicioIn,
    ServicioOut,
)


class TourismError(Exception):
    """Error de dominio del módulo turismo."""


class NotFound(TourismError):
    pass


class Conflict(TourismError):
    pass


# ---------------- helpers ----------------

def _geo_to_wkt(geo: GeoPoint | None) -> WKTElement | None:
    if geo is None:
        return None
    lon, lat = geo.coordinates[0], geo.coordinates[1]
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def _geojson_str_to_geopoint(geojson_str: str | None) -> GeoPoint | None:
    if not geojson_str:
        return None
    try:
        data = json.loads(geojson_str)
        if data.get("type") != "Point":
            return None
        return GeoPoint(type="Point", coordinates=data["coordinates"])
    except (ValueError, KeyError, TypeError):
        return None


async def _get_ubicacion_geojson(
    db: AsyncSession, tabla: str, id_value: UUID
) -> str | None:
    """Lee la columna `ubicacion` como string GeoJSON."""
    from sqlalchemy import text
    sql = text(f"SELECT ST_AsGeoJSON(ubicacion) AS geojson FROM {tabla} WHERE id = :id")
    result = await db.execute(sql, {"id": id_value})
    row = result.first()
    if row is None or row[0] is None:
        return None
    return row[0]


# =====================================================
#               RECURSOS TURÍSTICOS
# =====================================================

async def crear_recurso(
    db: AsyncSession, payload: RecursoTuristicoIn, created_by: UUID | None = None
) -> RecursoTuristico:
    obj = RecursoTuristico(
        urn=payload.urn,
        nombre=payload.nombre,
        categoria=payload.categoria,
        descripcion_corta=payload.descripcion_corta,
        nombre_i18n=payload.nombre_i18n.model_dump(exclude_none=True) if payload.nombre_i18n else None,
        descripcion_i18n=payload.descripcion_i18n.model_dump(exclude_none=True) if payload.descripcion_i18n else None,
        ubicacion=_geo_to_wkt(payload.ubicacion),
        direccion=payload.direccion,
        municipio=payload.municipio,
        codigo_postal=payload.codigo_postal,
        telefono=payload.telefono,
        email=payload.email,
        web=str(payload.web) if payload.web else None,
        horario=payload.horario,
        accesibilidad=payload.accesibilidad,
        servicios_disponibles=payload.servicios_disponibles,
        etiquetas=payload.etiquetas,
        imagenes=payload.imagenes,
        enlaces_externos=payload.enlaces_externos,
        activo=payload.activo,
        publicado=payload.publicado,
        metadata_adicional=None,
    )
    obj.created_by = created_by
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(f"Recurso con URN duplicado: {payload.urn}") from exc
    await db.refresh(obj)
    return obj


async def listar_recursos(
    db: AsyncSession, filtros: RecursoTuristicoFilter, page: PageParams
) -> tuple[list[RecursoTuristico], int]:
    base = select(RecursoTuristico).where(RecursoTuristico.deleted_at.is_(None))

    if filtros.categoria:
        base = base.where(RecursoTuristico.categoria == filtros.categoria)
    if filtros.municipio:
        base = base.where(RecursoTuristico.municipio == filtros.municipio)
    if filtros.publicado is not None:
        base = base.where(RecursoTuristico.publicado == filtros.publicado)

    if filtros.cerca_de_lat is not None and filtros.cerca_de_lon is not None:
        radio = filtros.radio_metros or 5000
        punto = ST_GeogFromText(
            f"SRID=4326;POINT({filtros.cerca_de_lon} {filtros.cerca_de_lat})"
        )
        base = base.where(ST_DWithin(RecursoTuristico.ubicacion, punto, radio))

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )

    res = await db.execute(
        base.order_by(RecursoTuristico.nombre).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


async def obtener_recurso(db: AsyncSession, recurso_id: UUID) -> RecursoTuristico:
    obj = await db.get(RecursoTuristico, recurso_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFound(f"Recurso {recurso_id} no encontrado")
    return obj


async def actualizar_recurso(
    db: AsyncSession,
    recurso_id: UUID,
    payload: RecursoTuristicoIn,
    updated_by: UUID | None = None,
) -> RecursoTuristico:
    obj = await obtener_recurso(db, recurso_id)
    obj.urn = payload.urn
    obj.nombre = payload.nombre
    obj.categoria = payload.categoria
    obj.descripcion_corta = payload.descripcion_corta
    obj.nombre_i18n = (
        payload.nombre_i18n.model_dump(exclude_none=True) if payload.nombre_i18n else None
    )
    obj.descripcion_i18n = (
        payload.descripcion_i18n.model_dump(exclude_none=True) if payload.descripcion_i18n else None
    )
    obj.ubicacion = _geo_to_wkt(payload.ubicacion)
    obj.direccion = payload.direccion
    obj.municipio = payload.municipio
    obj.codigo_postal = payload.codigo_postal
    obj.telefono = payload.telefono
    obj.email = payload.email
    obj.web = str(payload.web) if payload.web else None
    obj.horario = payload.horario
    obj.accesibilidad = payload.accesibilidad
    obj.servicios_disponibles = payload.servicios_disponibles
    obj.etiquetas = payload.etiquetas
    obj.imagenes = payload.imagenes
    obj.enlaces_externos = payload.enlaces_externos
    obj.activo = payload.activo
    obj.publicado = payload.publicado
    obj.updated_by = updated_by
    await db.flush()
    await db.refresh(obj)
    return obj


async def eliminar_recurso(
    db: AsyncSession, recurso_id: UUID, deleted_by: UUID | None = None
) -> None:
    obj = await obtener_recurso(db, recurso_id)
    obj.deleted_at = datetime.utcnow()
    obj.publicado = False
    obj.activo = False
    obj.updated_by = deleted_by
    await db.flush()


async def recurso_to_out(db: AsyncSession, r: RecursoTuristico) -> RecursoTuristicoOut:
    """Convierte un ORM RecursoTuristico al esquema de salida con GeoJSON."""
    geojson = await _get_ubicacion_geojson(db, "recursos_turisticos", r.id)
    return RecursoTuristicoOut(
        id=r.id,
        urn=r.urn,
        nombre=r.nombre,
        categoria=r.categoria,
        descripcion_corta=r.descripcion_corta,
        nombre_i18n=r.nombre_i18n,
        descripcion_i18n=r.descripcion_i18n,
        ubicacion=_geojson_str_to_geopoint(geojson),
        direccion=r.direccion,
        municipio=r.municipio,
        codigo_postal=r.codigo_postal,
        telefono=r.telefono,
        email=r.email,
        web=r.web,
        horario=r.horario,
        accesibilidad=r.accesibilidad,
        servicios_disponibles=r.servicios_disponibles,
        etiquetas=r.etiquetas,
        imagenes=r.imagenes,
        enlaces_externos=r.enlaces_externos,
        activo=r.activo,
        publicado=r.publicado,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# =====================================================
#               EVENTOS TURÍSTICOS
# =====================================================

async def crear_evento(
    db: AsyncSession, payload: EventoTuristicoIn, created_by: UUID | None = None
) -> EventoTuristico:
    obj = EventoTuristico(
        urn=payload.urn,
        nombre=payload.nombre,
        tipo=payload.tipo,
        descripcion=payload.descripcion,
        nombre_i18n=payload.nombre_i18n.model_dump(exclude_none=True) if payload.nombre_i18n else None,
        descripcion_i18n=payload.descripcion_i18n.model_dump(exclude_none=True) if payload.descripcion_i18n else None,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        recurso_id=payload.recurso_id,
        ubicacion=_geo_to_wkt(payload.ubicacion),
        direccion=payload.direccion,
        organizador=payload.organizador,
        precio=payload.precio,
        capacidad_aforo=payload.capacidad_aforo,
        enlace_inscripcion=str(payload.enlace_inscripcion) if payload.enlace_inscripcion else None,
        imagenes=payload.imagenes,
        etiquetas=payload.etiquetas,
        fuente=payload.fuente,
        activo=payload.activo,
        publicado=payload.publicado,
        metadata_adicional=None,
    )
    obj.created_by = created_by
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(f"Evento con URN duplicado: {payload.urn}") from exc
    await db.refresh(obj)
    return obj


async def listar_eventos(
    db: AsyncSession, filtros: EventoFilter, page: PageParams
) -> tuple[list[EventoTuristico], int]:
    base = select(EventoTuristico).where(EventoTuristico.deleted_at.is_(None))
    if filtros.desde:
        base = base.where(EventoTuristico.fecha_fin >= filtros.desde)
    if filtros.hasta:
        base = base.where(EventoTuristico.fecha_inicio <= filtros.hasta)
    if filtros.tipo:
        base = base.where(EventoTuristico.tipo == filtros.tipo)
    if filtros.publicado is not None:
        base = base.where(EventoTuristico.publicado == filtros.publicado)

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )

    res = await db.execute(
        base.order_by(EventoTuristico.fecha_inicio).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


async def obtener_evento(db: AsyncSession, evento_id: UUID) -> EventoTuristico:
    obj = await db.get(EventoTuristico, evento_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFound(f"Evento {evento_id} no encontrado")
    return obj


async def evento_to_out(db: AsyncSession, e: EventoTuristico) -> EventoTuristicoOut:
    geojson = await _get_ubicacion_geojson(db, "eventos_turisticos", e.id)
    return EventoTuristicoOut(
        id=e.id,
        urn=e.urn,
        nombre=e.nombre,
        tipo=e.tipo,
        descripcion=e.descripcion,
        nombre_i18n=e.nombre_i18n,
        descripcion_i18n=e.descripcion_i18n,
        fecha_inicio=e.fecha_inicio,
        fecha_fin=e.fecha_fin,
        recurso_id=e.recurso_id,
        ubicacion=_geojson_str_to_geopoint(geojson),
        direccion=e.direccion,
        organizador=e.organizador,
        precio=e.precio,
        capacidad_aforo=e.capacidad_aforo,
        enlace_inscripcion=e.enlace_inscripcion,
        imagenes=e.imagenes,
        etiquetas=e.etiquetas,
        fuente=e.fuente,
        activo=e.activo,
        publicado=e.publicado,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


# =====================================================
#                   SERVICIOS
# =====================================================

async def crear_servicio(
    db: AsyncSession, payload: ServicioIn, created_by: UUID | None = None
) -> Servicio:
    obj = Servicio(
        urn=payload.urn,
        nombre=payload.nombre,
        tipo=payload.tipo,
        descripcion=payload.descripcion,
        nombre_i18n=payload.nombre_i18n.model_dump(exclude_none=True) if payload.nombre_i18n else None,
        descripcion_i18n=payload.descripcion_i18n.model_dump(exclude_none=True) if payload.descripcion_i18n else None,
        ubicacion=_geo_to_wkt(payload.ubicacion),
        direccion=payload.direccion,
        municipio=payload.municipio,
        codigo_postal=payload.codigo_postal,
        telefono=payload.telefono,
        email=payload.email,
        web=str(payload.web) if payload.web else None,
        horario=payload.horario,
        rango_precios=payload.rango_precios,
        valoracion_media=payload.valoracion_media,
        registro_turismo=payload.registro_turismo,
        cif=payload.cif,
        accesibilidad=payload.accesibilidad,
        idiomas_atencion=payload.idiomas_atencion,
        etiquetas=payload.etiquetas,
        imagenes=payload.imagenes,
        activo=payload.activo,
        publicado=payload.publicado,
        metadata_adicional=None,
    )
    obj.created_by = created_by
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(f"Servicio con URN duplicado: {payload.urn}") from exc
    await db.refresh(obj)
    return obj


async def listar_servicios(
    db: AsyncSession, filtros: ServicioFilter, page: PageParams
) -> tuple[list[Servicio], int]:
    base = select(Servicio).where(Servicio.deleted_at.is_(None))
    if filtros.tipo:
        base = base.where(Servicio.tipo == filtros.tipo)
    if filtros.municipio:
        base = base.where(Servicio.municipio == filtros.municipio)
    if filtros.publicado is not None:
        base = base.where(Servicio.publicado == filtros.publicado)

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )

    res = await db.execute(
        base.order_by(Servicio.nombre).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


async def obtener_servicio(db: AsyncSession, servicio_id: UUID) -> Servicio:
    obj = await db.get(Servicio, servicio_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFound(f"Servicio {servicio_id} no encontrado")
    return obj


async def servicio_to_out(db: AsyncSession, s: Servicio) -> ServicioOut:
    geojson = await _get_ubicacion_geojson(db, "servicios", s.id)
    return ServicioOut(
        id=s.id,
        urn=s.urn,
        nombre=s.nombre,
        tipo=s.tipo,
        descripcion=s.descripcion,
        nombre_i18n=s.nombre_i18n,
        descripcion_i18n=s.descripcion_i18n,
        ubicacion=_geojson_str_to_geopoint(geojson),
        direccion=s.direccion,
        municipio=s.municipio,
        codigo_postal=s.codigo_postal,
        telefono=s.telefono,
        email=s.email,
        web=s.web,
        horario=s.horario,
        rango_precios=s.rango_precios,
        valoracion_media=float(s.valoracion_media) if s.valoracion_media is not None else None,
        registro_turismo=s.registro_turismo,
        cif=s.cif,
        accesibilidad=s.accesibilidad,
        idiomas_atencion=s.idiomas_atencion,
        etiquetas=s.etiquetas,
        imagenes=s.imagenes,
        activo=s.activo,
        publicado=s.publicado,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )
