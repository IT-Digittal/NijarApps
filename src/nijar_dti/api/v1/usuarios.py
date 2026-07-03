"""Endpoints de gestión de usuarios del CMS (solo administrador_tic)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.core.database import get_db
from nijar_dti.models.usuario import RolUsuario
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.usuarios import UsuarioInviteRequest, UsuarioResponse
from nijar_dti.services import usuarios_service

router = APIRouter()

_solo_admin_tic = require_roles(RolUsuario.ADMINISTRADOR_TIC.value)


@router.get(
    "",
    response_model=list[UsuarioResponse],
    summary="Listar usuarios del CMS",
)
async def listar(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_solo_admin_tic),
) -> list[UsuarioResponse]:
    usuarios = await usuarios_service.listar_usuarios(db)
    return [UsuarioResponse.model_validate(u) for u in usuarios]


@router.post(
    "/invitar",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invitar (crear) un nuevo usuario del CMS",
)
async def invitar(
    payload: UsuarioInviteRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> UsuarioResponse:
    try:
        nuevo = await usuarios_service.invitar_usuario(
            db,
            email=payload.email,
            nombre_completo=payload.nombre_completo,
            rol=payload.rol,
        )
    except usuarios_service.UsuarioYaExisteError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UsuarioResponse.model_validate(nuevo)
