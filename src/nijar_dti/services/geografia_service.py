"""Lógica de negocio de las capas geográficas del gemelo 2D.

Sirve el catálogo de capas y cada capa como GeoJSON `FeatureCollection`
(geometría serializada con `ST_AsGeoJSON`), y resuelve la parcela catastral
que contiene un punto (`ST_Contains`) — la base para vincular los registros
georreferenciados de la plataforma con su referencia catastral.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.geografia import CapaGeografica, ElementoGeografico, GrupoCapa
from nijar_dti.schemas.geografia import (
    CapaGeograficaOut,
    CapaGeograficaUpdate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    ParcelaCatastralOut,
)


class GeografiaError(Exception):
    """Error de dominio del módulo de capas geográficas."""


class CapaNoEncontradaError(GeografiaError):
    """La capa solicitada no existe o no está activa."""


def _geojson(valor: str | None) -> dict[str, Any] | None:
    if not valor:
        return None
    try:
        obj = json.loads(valor)
    except (ValueError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


def _capa_out(capa: CapaGeografica, n_elementos: int) -> CapaGeograficaOut:
    out = CapaGeograficaOut.model_validate(capa)
    out.n_elementos = n_elementos
    return out


async def listar_capas(db: AsyncSession, solo_activas: bool = True) -> list[CapaGeograficaOut]:
    """Catálogo de capas ordenado por grupo y orden, con conteo de elementos."""
    n_elementos = (
        select(
            ElementoGeografico.capa_id,
            func.count().label("n"),
        )
        .group_by(ElementoGeografico.capa_id)
        .subquery()
    )
    consulta = (
        select(CapaGeografica, func.coalesce(n_elementos.c.n, 0))
        .outerjoin(n_elementos, n_elementos.c.capa_id == CapaGeografica.id)
        .order_by(CapaGeografica.grupo, CapaGeografica.orden, CapaGeografica.nombre)
    )
    if solo_activas:
        consulta = consulta.where(CapaGeografica.activa.is_(True))
    filas = (await db.execute(consulta)).all()
    return [_capa_out(capa, int(n)) for capa, n in filas]


async def capa_geojson(db: AsyncSession, codigo: str) -> GeoJSONFeatureCollection:
    """Devuelve una capa como `FeatureCollection` GeoJSON con su estilo."""
    capa = (
        await db.execute(select(CapaGeografica).where(CapaGeografica.codigo == codigo))
    ).scalar_one_or_none()
    if capa is None or not capa.activa:
        raise CapaNoEncontradaError(codigo)

    filas = (
        await db.execute(
            select(
                ElementoGeografico.id,
                ElementoGeografico.nombre,
                ElementoGeografico.codigo,
                ElementoGeografico.referencia_catastral,
                ElementoGeografico.propiedades,
                func.ST_AsGeoJSON(ElementoGeografico.geometria),
            )
            .where(ElementoGeografico.capa_id == capa.id)
            .order_by(ElementoGeografico.orden, ElementoGeografico.nombre)
        )
    ).all()

    features: list[GeoJSONFeature] = []
    for _id, nombre, cod, refcat, props, geojson in filas:
        propiedades = dict(props or {})
        propiedades.setdefault("nombre", nombre)
        if cod:
            propiedades.setdefault("codigo", cod)
        if refcat:
            propiedades.setdefault("referencia_catastral", refcat)
        features.append(
            GeoJSONFeature(id=str(_id), geometry=_geojson(geojson), properties=propiedades)
        )

    return GeoJSONFeatureCollection(
        capa=_capa_out(capa, len(features)),
        features=features,
    )


async def parcela_en_punto(
    db: AsyncSession, lat: float, lon: float, grupo: str = GrupoCapa.CATASTRO
) -> ParcelaCatastralOut | None:
    """Resuelve la parcela/elemento de un grupo que contiene un punto.

    Point-in-polygon con `ST_Contains`. Pensado para el grupo «catastro», es el
    mecanismo para asociar cada registro georreferenciado (recurso, sensor,
    contenedor…) con su parcela cuando se carguen los datos catastrales.
    """
    punto = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    fila = (
        await db.execute(
            select(
                ElementoGeografico.nombre,
                ElementoGeografico.referencia_catastral,
                ElementoGeografico.propiedades,
                CapaGeografica.nombre,
                func.ST_AsGeoJSON(ElementoGeografico.geometria),
            )
            .join(CapaGeografica, CapaGeografica.id == ElementoGeografico.capa_id)
            .where(
                CapaGeografica.grupo == grupo,
                CapaGeografica.activa.is_(True),
                func.ST_Contains(ElementoGeografico.geometria, punto),
            )
            .limit(1)
        )
    ).first()
    if fila is None:
        return None
    nombre, refcat, props, capa_nombre, geojson = fila
    return ParcelaCatastralOut(
        referencia_catastral=refcat,
        nombre=nombre,
        capa=capa_nombre,
        propiedades=dict(props or {}),
        geometry=_geojson(geojson),
    )


async def _capa_por_codigo(db: AsyncSession, codigo: str) -> CapaGeografica:
    capa = (
        await db.execute(select(CapaGeografica).where(CapaGeografica.codigo == codigo))
    ).scalar_one_or_none()
    if capa is None:
        raise CapaNoEncontradaError(codigo)
    return capa


async def _n_elementos(db: AsyncSession, capa: CapaGeografica) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(ElementoGeografico)
                .where(ElementoGeografico.capa_id == capa.id)
            )
        ).scalar_one()
        or 0
    )


async def actualizar_capa(
    db: AsyncSession, codigo: str, cambios: CapaGeograficaUpdate
) -> CapaGeograficaOut:
    """Actualiza estilo, orden y visibilidad de una capa (no su geometría)."""
    capa = await _capa_por_codigo(db, codigo)
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        setattr(capa, campo, valor)
    await db.flush()
    return _capa_out(capa, await _n_elementos(db, capa))


async def eliminar_capa(db: AsyncSession, codigo: str) -> int:
    """Elimina una capa y todos sus elementos. Devuelve cuántos elementos borró."""
    capa = await _capa_por_codigo(db, codigo)
    n = await _n_elementos(db, capa)
    await db.execute(delete(ElementoGeografico).where(ElementoGeografico.capa_id == capa.id))
    await db.delete(capa)
    await db.flush()
    return n
