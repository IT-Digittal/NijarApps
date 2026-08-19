"""Endpoints de gestión de usuarios, roles y permisos (solo administrador_tic)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.core.database import get_db
from nijar_dti.models.usuario import RolUsuario, Usuario
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.usuarios import (
    MatrizPermisos,
    PasswordTemporalResponse,
    UsuarioInviteRequest,
    UsuarioResponse,
    UsuarioUpdateRequest,
)
from nijar_dti.services import roles_service, usuarios_service

router = APIRouter()

_solo_admin_tic = require_roles(RolUsuario.ADMINISTRADOR_TIC.value)


async def _actor(db: AsyncSession, current: CurrentUser) -> Usuario:
    """Recupera la entidad Usuario del actor autenticado (para auditoría/guardas)."""
    return await usuarios_service.obtener_usuario(db, current.id)


async def _validar_rol(db: AsyncSession, slug: str) -> None:
    """Rechaza asignar un rol que no existe en la tabla de roles."""
    if not await roles_service.existe_rol(db, slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol '{slug}' no existe.",
        )


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


@router.get(
    "/matriz-permisos",
    response_model=MatrizPermisos,
    summary="Matriz de permisos (roles × módulos)",
)
async def matriz_permisos(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_solo_admin_tic),
) -> MatrizPermisos:
    return MatrizPermisos.model_validate(await roles_service.matriz(db))


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
    await _validar_rol(db, payload.rol)
    try:
        actor = await _actor(db, current)
        nuevo = await usuarios_service.invitar_usuario(
            db,
            email=payload.email,
            nombre_completo=payload.nombre_completo,
            rol=payload.rol,
            invitado_por=actor,
        )
    except usuarios_service.UsuarioYaExisteError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UsuarioResponse.model_validate(nuevo)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Editar un usuario (nombre, rol y/o estado)",
)
async def actualizar(
    usuario_id: UUID,
    payload: UsuarioUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> UsuarioResponse:
    if payload.rol is not None:
        await _validar_rol(db, payload.rol)
    try:
        actor = await _actor(db, current)
        actualizado = await usuarios_service.actualizar_usuario(
            db,
            usuario_id,
            nombre_completo=payload.nombre_completo,
            rol=payload.rol,
            activo=payload.activo,
            actor=actor,
        )
    except usuarios_service.UsuarioNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except usuarios_service.OperacionNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UsuarioResponse.model_validate(actualizado)


@router.post(
    "/{usuario_id}/activar",
    response_model=UsuarioResponse,
    summary="Activar una cuenta",
)
async def activar(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> UsuarioResponse:
    return await _cambiar_estado(db, current, usuario_id, activo=True)


@router.post(
    "/{usuario_id}/desactivar",
    response_model=UsuarioResponse,
    summary="Desactivar una cuenta",
)
async def desactivar(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> UsuarioResponse:
    return await _cambiar_estado(db, current, usuario_id, activo=False)


async def _cambiar_estado(
    db: AsyncSession, current: CurrentUser, usuario_id: UUID, *, activo: bool
) -> UsuarioResponse:
    try:
        actor = await _actor(db, current)
        usuario = await usuarios_service.cambiar_estado(db, usuario_id, activo=activo, actor=actor)
    except usuarios_service.UsuarioNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except usuarios_service.OperacionNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UsuarioResponse.model_validate(usuario)


@router.post(
    "/{usuario_id}/reset-password",
    response_model=PasswordTemporalResponse,
    summary="Restablecer la contraseña (genera una temporal)",
)
async def reset_password(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> PasswordTemporalResponse:
    try:
        actor = await _actor(db, current)
        usuario, temporal = await usuarios_service.restablecer_password(db, usuario_id, actor=actor)
    except usuarios_service.UsuarioNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PasswordTemporalResponse(id=usuario.id, email=usuario.email, password_temporal=temporal)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (borrado lógico) una cuenta",
)
async def eliminar(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_solo_admin_tic),
) -> None:
    try:
        actor = await _actor(db, current)
        await usuarios_service.eliminar_usuario(db, usuario_id, actor=actor)
    except usuarios_service.UsuarioNoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except usuarios_service.OperacionNoPermitidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
