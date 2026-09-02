"""Lógica de negocio de las capas geográficas del gemelo 2D.

Sirve el catálogo de capas y cada capa como GeoJSON `FeatureCollection`
(geometría serializada con `ST_AsGeoJSON`), y resuelve la parcela catastral
que contiene un punto (`ST_Contains`) — la base para vincular los registros
georreferenciados de la plataforma con su referencia catastral.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.geografia import (
    CapaGeografica,
    ElementoGeografico,
    GrupoCapa,
    MedicionGemelo,
    TipoMedicion,
)
from nijar_dti.schemas.geografia import (
    CapaGeograficaOut,
    CapaGeograficaUpdate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    MedicionGemeloIn,
    MedicionGemeloOut,
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


# ---------- Mediciones guardadas de la regla del gemelo ----------

_RADIO_TIERRA_M = 6371008.8  # radio medio (IUGG), el mismo que usa el frontend


class MedicionNoEncontradaError(GeografiaError):
    """La medición solicitada no existe."""


class MedicionAjenaError(GeografiaError):
    """El usuario no puede borrar una medición que no es suya."""


def distancia_geodesica_m(puntos: Sequence[tuple[float, float]]) -> float:
    """Distancia acumulada (haversine) de una polilínea [[lat, lon], ...]."""
    total = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(puntos, puntos[1:], strict=False):
        f1, f2 = math.radians(lat1), math.radians(lat2)
        df = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
        total += 2 * _RADIO_TIERRA_M * math.asin(math.sqrt(a))
    return total


def area_esferica_m2(puntos: Sequence[tuple[float, float]]) -> float:
    """Área del polígono [[lat, lon], ...] por exceso esférico (anillo cerrado)."""
    s = 0.0
    n = len(puntos)
    for i in range(n):
        lat1, lon1 = puntos[i]
        lat2, lon2 = puntos[(i + 1) % n]
        s += math.radians(lon2 - lon1) * (
            2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2))
        )
    return abs(s * _RADIO_TIERRA_M * _RADIO_TIERRA_M / 2)


async def listar_mediciones(db: AsyncSession) -> list[MedicionGemeloOut]:
    filas = (
        (await db.execute(select(MedicionGemelo).order_by(MedicionGemelo.created_at.desc())))
        .scalars()
        .all()
    )
    return [MedicionGemeloOut.model_validate(m) for m in filas]


async def crear_medicion(
    db: AsyncSession, datos: MedicionGemeloIn, creado_por: str | None
) -> MedicionGemeloOut:
    """Guarda una medición; distancia y área se recalculan en el servidor."""
    puntos = [(float(lat), float(lon)) for lat, lon in datos.puntos]
    es_poligono = datos.tipo == TipoMedicion.POLIGONO.value and len(puntos) >= 3
    distancia = distancia_geodesica_m(puntos)
    if es_poligono:
        distancia += distancia_geodesica_m([puntos[-1], puntos[0]])
    medicion = MedicionGemelo(
        nombre=datos.nombre.strip(),
        tipo=TipoMedicion.POLIGONO if es_poligono else TipoMedicion.LINEA,
        puntos=[[lat, lon] for lat, lon in puntos],
        distancia_m=round(distancia, 2),
        area_m2=round(area_esferica_m2(puntos), 2) if es_poligono else None,
        creado_por=creado_por,
    )
    db.add(medicion)
    await db.flush()
    return MedicionGemeloOut.model_validate(medicion)


async def eliminar_medicion(
    db: AsyncSession, medicion_id: UUID, email: str, es_editor: bool
) -> None:
    """Borra una medición: su autor siempre; el resto, solo perfiles editores."""
    medicion = (
        await db.execute(select(MedicionGemelo).where(MedicionGemelo.id == medicion_id))
    ).scalar_one_or_none()
    if medicion is None:
        raise MedicionNoEncontradaError(str(medicion_id))
    if not es_editor and medicion.creado_por != email:
        raise MedicionAjenaError(str(medicion_id))
    await db.delete(medicion)
    await db.flush()
