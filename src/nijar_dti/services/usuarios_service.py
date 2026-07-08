"""Lógica de negocio para gestión de usuarios del CMS."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.security import hash_password
from nijar_dti.models.usuario import RolUsuario, Usuario


class UsuarioYaExisteError(Exception):
    """El email ya está registrado como usuario activo."""


class UsuarioNoEncontradoError(Exception):
    """No existe un usuario con el identificador indicado."""


class OperacionNoPermitidaError(Exception):
    """La operación dejaría el sistema en un estado no permitido.

    Por ejemplo: desactivarse/borrarse a uno mismo, o dejar la plataforma sin
    ningún administrador TIC activo.
    """


async def listar_usuarios(db: AsyncSession) -> list[Usuario]:
    """Devuelve todos los usuarios no borrados (activos e inactivos)."""
    result = await db.execute(
        select(Usuario).where(Usuario.deleted_at.is_(None)).order_by(Usuario.created_at)
    )
    return list(result.scalars().all())


async def invitar_usuario(
    db: AsyncSession,
    email: str,
    nombre_completo: str,
    rol: str,
    invitado_por: Usuario | None = None,
) -> Usuario:
    """Crea un usuario nuevo con contraseña temporal aleatoria.

    El usuario queda activo pero con `requiere_2fa=True`, de modo que en el
    primer acceso deberá configurar la MFA y restablecer la contraseña.
    En una implementación completa se enviaría un email con el token de alta.
    """
    existing = await db.execute(
        select(Usuario)
        .where(Usuario.email == email)
        .where(Usuario.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none() is not None:
        raise UsuarioYaExisteError(f"Ya existe un usuario con email {email}")

    contrasena_temporal = secrets.token_urlsafe(24)

    nuevo = Usuario(
        email=email,
        nombre_completo=nombre_completo,
        password_hash=hash_password(contrasena_temporal),
        rol=rol,
        scopes_adicionales=[],
        activo=True,
        requiere_2fa=True,
        created_by=invitado_por.id if invitado_por else None,
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo


async def obtener_usuario(db: AsyncSession, usuario_id: UUID) -> Usuario:
    """Devuelve un usuario no borrado por su id o lanza si no existe."""
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None or usuario.deleted_at is not None:
        raise UsuarioNoEncontradoError(f"No existe el usuario {usuario_id}")
    return usuario


async def _admins_activos(db: AsyncSession, excluir: UUID | None = None) -> int:
    """Cuenta administradores TIC activos (opcionalmente excluyendo uno)."""
    stmt = (
        select(func.count())
        .select_from(Usuario)
        .where(Usuario.rol == RolUsuario.ADMINISTRADOR_TIC.value)
        .where(Usuario.activo.is_(True))
        .where(Usuario.deleted_at.is_(None))
    )
    if excluir is not None:
        stmt = stmt.where(Usuario.id != excluir)
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def actualizar_usuario(
    db: AsyncSession,
    usuario_id: UUID,
    *,
    nombre_completo: str | None = None,
    rol: str | None = None,
    activo: bool | None = None,
    actor: Usuario | None = None,
) -> Usuario:
    """Edita nombre, rol y/o estado de un usuario aplicando las guardas.

    No permite que un actor se desactive a sí mismo, ni que la operación deje
    la plataforma sin ningún administrador TIC activo.
    """
    usuario = await obtener_usuario(db, usuario_id)
    es_uno_mismo = actor is not None and actor.id == usuario.id

    # ¿La operación retira privilegios/actividad al último admin?
    quita_admin = (
        usuario.rol == RolUsuario.ADMINISTRADOR_TIC.value
        and (
            (rol is not None and rol != RolUsuario.ADMINISTRADOR_TIC)
            or (activo is False)
        )
    )
    if quita_admin and await _admins_activos(db, excluir=usuario.id) == 0:
        raise OperacionNoPermitidaError(
            "No se puede dejar la plataforma sin ningún administrador TIC activo."
        )
    if activo is False and es_uno_mismo:
        raise OperacionNoPermitidaError("No puedes desactivar tu propia cuenta.")

    if nombre_completo is not None:
        usuario.nombre_completo = nombre_completo
    if rol is not None:
        usuario.rol = rol
    if activo is not None:
        usuario.activo = activo
    if actor is not None:
        usuario.updated_by = actor.id

    await db.commit()
    await db.refresh(usuario)
    return usuario


async def cambiar_estado(
    db: AsyncSession,
    usuario_id: UUID,
    *,
    activo: bool,
    actor: Usuario | None = None,
) -> Usuario:
    """Activa o desactiva una cuenta (atajo sobre `actualizar_usuario`)."""
    return await actualizar_usuario(db, usuario_id, activo=activo, actor=actor)


async def restablecer_password(
    db: AsyncSession,
    usuario_id: UUID,
    actor: Usuario | None = None,
) -> tuple[Usuario, str]:
    """Genera una contraseña temporal nueva y devuelve (usuario, contraseña).

    La contraseña en claro solo se devuelve una vez, para mostrarla al admin.
    """
    usuario = await obtener_usuario(db, usuario_id)
    contrasena_temporal = secrets.token_urlsafe(24)
    usuario.password_hash = hash_password(contrasena_temporal)
    usuario.requiere_2fa = True
    if actor is not None:
        usuario.updated_by = actor.id
    await db.commit()
    await db.refresh(usuario)
    return usuario, contrasena_temporal


async def eliminar_usuario(
    db: AsyncSession,
    usuario_id: UUID,
    actor: Usuario | None = None,
) -> None:
    """Borrado lógico (soft-delete) de una cuenta, con las mismas guardas."""
    usuario = await obtener_usuario(db, usuario_id)
    if actor is not None and actor.id == usuario.id:
        raise OperacionNoPermitidaError("No puedes eliminar tu propia cuenta.")
    if (
        usuario.rol == RolUsuario.ADMINISTRADOR_TIC.value
        and usuario.activo
        and await _admins_activos(db, excluir=usuario.id) == 0
    ):
        raise OperacionNoPermitidaError(
            "No se puede eliminar al último administrador TIC activo."
        )

    usuario.activo = False
    usuario.deleted_at = datetime.now(UTC)
    if actor is not None:
        usuario.updated_by = actor.id
    await db.commit()
