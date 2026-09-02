"""Endpoints de las capas geográficas del gemelo 2D.

Sirve la cartografía vectorial por capas (planeamiento urbanístico, parcelario
catastral, clasificación del suelo…) que el Gemelo vivo 2D pinta sobre el mapa,
al estilo de un geoportal municipal de urbanismo.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.models.usuario import RolUsuario
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.geografia import (
    CapaGeograficaOut,
    CapaGeograficaUpdate,
    GeoJSONFeatureCollection,
    MedicionGemeloIn,
    MedicionGemeloOut,
    ParcelaCatastralOut,
)
from nijar_dti.services import geografia_service as svc

router = APIRouter()

# Gestión de capas: mismo perfil editor que el resto de contenidos del panel
_editores_capas = require_roles(
    RolUsuario.ADMINISTRADOR_TIC.value,
    RolUsuario.GESTOR_CONTENIDOS.value,
)


@router.get(
    "/capas",
    response_model=list[CapaGeograficaOut],
    summary="Catálogo de capas geográficas del gemelo 2D",
)
async def listar_capas(
    incluir_inactivas: bool = Query(
        False, description="Incluir capas desactivadas (vista de gestión)"
    ),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[CapaGeograficaOut]:
    return await svc.listar_capas(db, solo_activas=not incluir_inactivas)


@router.put(
    "/capas/{codigo}",
    response_model=CapaGeograficaOut,
    summary="Editar estilo, orden y visibilidad de una capa",
)
async def actualizar_capa(
    codigo: str,
    cambios: CapaGeograficaUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_editores_capas),
) -> CapaGeograficaOut:
    try:
        return await svc.actualizar_capa(db, codigo, cambios)
    except svc.CapaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=f"Capa '{codigo}' no encontrada") from exc


@router.delete(
    "/capas/{codigo}",
    summary="Eliminar una capa y todos sus elementos",
)
async def eliminar_capa(
    codigo: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_editores_capas),
) -> dict[str, int | str]:
    try:
        n = await svc.eliminar_capa(db, codigo)
    except svc.CapaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=f"Capa '{codigo}' no encontrada") from exc
    return {"codigo": codigo, "elementos_eliminados": n}


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


@router.get(
    "/mediciones",
    response_model=list[MedicionGemeloOut],
    summary="Mediciones guardadas de la regla del gemelo",
)
async def listar_mediciones(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[MedicionGemeloOut]:
    return await svc.listar_mediciones(db)


@router.post(
    "/mediciones",
    response_model=MedicionGemeloOut,
    status_code=201,
    summary="Guardar una medición de la regla del gemelo",
)
async def crear_medicion(
    datos: MedicionGemeloIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> MedicionGemeloOut:
    return await svc.crear_medicion(db, datos, creado_por=user.email)


@router.delete(
    "/mediciones/{medicion_id}",
    status_code=204,
    summary="Eliminar una medición guardada (su autor, o un perfil editor)",
)
async def eliminar_medicion(
    medicion_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    es_editor = user.rol in (
        RolUsuario.ADMINISTRADOR_TIC.value,
        RolUsuario.GESTOR_CONTENIDOS.value,
    )
    try:
        await svc.eliminar_medicion(db, medicion_id, email=user.email, es_editor=es_editor)
    except svc.MedicionNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail="Medición no encontrada") from exc
    except svc.MedicionAjenaError as exc:
        raise HTTPException(
            status_code=403,
            detail="Solo el autor de la medición o un perfil editor pueden eliminarla",
        ) from exc
