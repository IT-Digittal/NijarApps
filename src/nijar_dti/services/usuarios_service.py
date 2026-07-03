"""Lógica de negocio para gestión de usuarios del CMS."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.security import hash_password
from nijar_dti.models.usuario import RolUsuario, Usuario


class UsuarioYaExisteError(Exception):
    """El email ya está registrado como usuario activo."""


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
    rol: RolUsuario,
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
