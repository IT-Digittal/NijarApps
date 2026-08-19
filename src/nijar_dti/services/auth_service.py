"""Lógica de negocio de autenticación."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from nijar_dti.models.usuario import Usuario


class AuthError(Exception):
    """Error genérico de autenticación."""


async def get_user_by_email(db: AsyncSession, email: str) -> Usuario | None:
    result = await db.execute(
        select(Usuario).where(Usuario.email == email).where(Usuario.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def authenticate(db: AsyncSession, email: str, password: str) -> Usuario:
    user = await get_user_by_email(db, email)
    if user is None or not user.activo:
        raise AuthError("Credenciales inválidas")
    if not verify_password(password, user.password_hash):
        raise AuthError("Credenciales inválidas")
    return user


def issue_tokens(user: Usuario) -> dict[str, str | int]:
    """Genera el par access+refresh para un usuario autenticado."""
    settings = get_settings()
    scopes = [user.rol]
    if user.scopes_adicionales:
        scopes.extend(user.scopes_adicionales)  # type: ignore[arg-type]
    access = create_access_token(subject=str(user.id), scopes=scopes)  # type: ignore[arg-type]
    refresh = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict[str, str | int]:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise AuthError("Refresh token inválido") from exc

    if payload.get("type") != "refresh":
        raise AuthError("Token no es de tipo refresh")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Token sin sujeto")

    from uuid import UUID

    try:
        uid = UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise AuthError("Token con sujeto inválido") from exc

    user = await db.get(Usuario, uid)
    if user is None or not user.activo or user.deleted_at is not None:
        raise AuthError("Usuario no encontrado o inactivo")
    return issue_tokens(user)
