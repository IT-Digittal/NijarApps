"""Endpoints de campañas de promoción turística (bloque 9)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.campanas import (
    CampanaIn,
    CampanaKPIs,
    CampanaOut,
    CampanaUpdate,
)
from nijar_dti.services import campanas_service as svc

router = APIRouter()

_GESTORES = ("administrador_tic", "gestor_contenidos")


@router.get(
    "",
    response_model=list[CampanaOut],
    summary="Listar campañas de promoción",
)
async def listar(
    estado: str | None = Query(None, pattern=r"^(planificada|activa|finalizada|cancelada)$"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[CampanaOut]:
    filas = await svc.listar_campanas(db, estado)
    return [CampanaOut.model_validate(c) for c in filas]


@router.post(
    "",
    response_model=CampanaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una campaña",
)
async def crear(
    payload: CampanaIn,
    user: Annotated[CurrentUser, Depends(require_roles(*_GESTORES))],
    db: AsyncSession = Depends(get_db),
) -> CampanaOut:
    campana = await svc.crear_campana(db, payload)
    return CampanaOut.model_validate(campana)


@router.get(
    "/{campana_id}",
    response_model=CampanaOut,
    summary="Detalle de una campaña",
)
async def detalle(
    campana_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CampanaOut:
    try:
        campana = await svc.obtener_campana(db, campana_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CampanaOut.model_validate(campana)


@router.put(
    "/{campana_id}",
    response_model=CampanaOut,
    summary="Actualizar una campaña",
)
async def actualizar(
    campana_id: UUID,
    payload: CampanaUpdate,
    user: Annotated[CurrentUser, Depends(require_roles(*_GESTORES))],
    db: AsyncSession = Depends(get_db),
) -> CampanaOut:
    try:
        campana = await svc.actualizar_campana(db, campana_id, payload)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CampanaOut.model_validate(campana)


@router.delete(
    "/{campana_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (soft delete) una campaña",
)
async def eliminar(
    campana_id: UUID,
    user: Annotated[CurrentUser, Depends(require_roles(*_GESTORES))],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await svc.eliminar_campana(db, campana_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{campana_id}/kpis",
    response_model=CampanaKPIs,
    summary="Eficacia de la campaña (menciones, visitas y comparativa)",
)
async def kpis(
    campana_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CampanaKPIs:
    try:
        campana = await svc.obtener_campana(db, campana_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await svc.calcular_kpis(db, campana)
