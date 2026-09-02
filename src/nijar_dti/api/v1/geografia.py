"""Endpoints de las capas geográficas del gemelo 2D.

Sirve la cartografía vectorial por capas (planeamiento urbanístico, parcelario
catastral, clasificación del suelo…) que el Gemelo vivo 2D pinta sobre el mapa,
al estilo de un geoportal municipal de urbanismo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.geografia import (
    CapaGeograficaOut,
    GeoJSONFeatureCollection,
    ParcelaCatastralOut,
)
from nijar_dti.services import geografia_service as svc

router = APIRouter()


@router.get(
    "/capas",
    response_model=list[CapaGeograficaOut],
    summary="Catálogo de capas geográficas del gemelo 2D",
)
async def listar_capas(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[CapaGeograficaOut]:
    return await svc.listar_capas(db)


@router.get(
    "/capas/{codigo}/geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Capa como FeatureCollection GeoJSON",
)
async def capa_geojson(
    codigo: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> GeoJSONFeatureCollection:
    try:
        return await svc.capa_geojson(db, codigo)
    except svc.CapaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=f"Capa '{codigo}' no encontrada") from exc


@router.get(
    "/catastro/parcela",
    response_model=ParcelaCatastralOut,
    summary="Parcela catastral que contiene un punto (point-in-polygon)",
)
async def parcela_en_punto(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ParcelaCatastralOut:
    parcela = await svc.parcela_en_punto(db, lat, lon)
    if parcela is None:
        raise HTTPException(
            status_code=404,
            detail="No hay parcela catastral cargada que contenga ese punto",
        )
    return parcela
