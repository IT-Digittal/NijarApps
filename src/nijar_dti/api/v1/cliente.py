"""Endpoints de la ficha general del cliente / Ayuntamiento (bloque 1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.cliente import ClienteIn, ClienteOut, ClienteUpdate
from nijar_dti.services import cliente_service as svc

router = APIRouter()


@router.get(
    "",
    response_model=ClienteOut,
    summary="Ficha general del cliente / Ayuntamiento",
)
async def obtener(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ClienteOut:
    cliente = await svc.obtener_cliente(db)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No hay ficha de cliente")
    return ClienteOut.model_validate(cliente)


@router.put(
    "",
    response_model=ClienteOut,
    summary="Crear o reemplazar la ficha del cliente",
)
async def guardar(
    payload: ClienteIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic"))],
    db: AsyncSession = Depends(get_db),
) -> ClienteOut:
    cliente = await svc.guardar_cliente(db, payload)
    return ClienteOut.model_validate(cliente)


@router.patch(
    "",
    response_model=ClienteOut,
    summary="Actualización parcial de la ficha del cliente",
)
async def actualizar(
    payload: ClienteUpdate,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic"))],
    db: AsyncSession = Depends(get_db),
) -> ClienteOut:
    try:
        cliente = await svc.actualizar_cliente(db, payload)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ClienteOut.model_validate(cliente)
