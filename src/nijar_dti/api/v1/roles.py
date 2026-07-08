"""Endpoints de gestión de roles y permisos (solo administrador_tic)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.core.database import get_db
from nijar_dti.models.rol import Rol
from nijar_dti.models.usuario import RolUsuario
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.roles import RolCreateRequest, RolResponse, RolUpdateRequest
from nijar_dti.services import roles_service, usuarios_service

router = APIRouter()

_solo_admin_tic = require_roles(RolUsuario.ADMINISTRADOR_TIC.value)


def _to_response(rol: Rol, n_usuarios: int) -> RolResponse:
    return RolResponse(
        slug=rol.slug,
        display=rol.display,
        descripcion=rol.descripcion,
        permisos=sorted(rol.permisos or []),
        es_sistema=rol.es_sistema,
        n_usuarios=n_usuarios,
    )


@router.get("", response_model=list[RolResponse], summary="Listar roles y sus permisos")
async def listar(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_solo_admin_tic),
) -> list[RolResponse]:
    roles = await roles_service.listar_roles(db)
    conteo = await roles_service.contar_usuarios_por_rol(db)
    return [_to_response(r, conteo.get(r.slug, 0)) for r in roles]


@router.post(
    "",
    response_model=RolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un rol nuevo",
)
async def crear(
    payload: RolCreateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> RolResponse:
    try:
        actor = await usuarios_service.obtener_usuario(db, current.id)
        rol = await roles_service.crear_rol(
            db,
            slug=payload.slug,
            display=payload.display,
            descripcion=payload.descripcion,
            permisos=payload.permisos,
            actor=actor,
        )
    except roles_service.RolYaExisteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except roles_service.OperacionRolNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(rol, 0)


@router.patch(
    "/{slug}",
    response_model=RolResponse,
    summary="Editar un rol (nombre, descripción y/o permisos)",
)
async def actualizar(
    slug: str,
    payload: RolUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> RolResponse:
    try:
        actor = await usuarios_service.obtener_usuario(db, current.id)
        rol = await roles_service.actualizar_rol(
            db,
            slug,
            display=payload.display,
            descripcion=payload.descripcion,
            permisos=payload.permisos,
            actor=actor,
        )
    except roles_service.RolNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except roles_service.OperacionRolNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    conteo = await roles_service.contar_usuarios_por_rol(db)
    return _to_response(rol, conteo.get(rol.slug, 0))


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un rol (solo roles no de sistema y sin usuarios)",
)
async def eliminar(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> None:
    try:
        actor = await usuarios_service.obtener_usuario(db, current.id)
        await roles_service.eliminar_rol(db, slug, actor=actor)
    except roles_service.RolNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except roles_service.OperacionRolNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
