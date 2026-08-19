"""Dependencias de FastAPI compartidas por los endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.database import get_db
from nijar_dti.core.security import decode_token
from nijar_dti.models.usuario import Usuario
from nijar_dti.schemas.auth import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Decodifica el JWT de acceso y devuelve el usuario actual."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no es de tipo access",
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sujeto")

    try:
        user_id = UUID(sub)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc

    user = await db.get(Usuario, user_id)
    if user is None or not user.activo or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")

    scopes = list(payload.get("scopes") or [])
    # Los permisos del rol se leen de BD en cada petición, de modo que un cambio
    # en la matriz surte efecto sin necesidad de re-login.
    from nijar_dti.services import roles_service

    permisos = sorted(await roles_service.permisos_de_rol(db, user.rol))
    return CurrentUser(
        id=user.id,
        email=user.email,
        nombre_completo=user.nombre_completo,
        rol=user.rol,
        scopes=scopes,
        permisos=permisos,
        activo=user.activo,
    )


def require_roles(*allowed_roles: str) -> Callable[..., Awaitable[CurrentUser]]:
    """Crea una dependencia que exige uno de los roles indicados."""

    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{user.rol}' no autorizado para esta operación",
            )
        return user

    return _dep


def require_permiso(*permisos_requeridos: str) -> Callable[..., Awaitable[CurrentUser]]:
    """Crea una dependencia que exige que el rol tenga TODOS los permisos dados.

    Los permisos se resuelven en `get_current_user` desde la matriz de roles en
    BD, por lo que un rol personalizado con módulos restringidos recibe 403 aunque
    llame directamente a la API.
    """

    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        faltan = [p for p in permisos_requeridos if p not in user.permisos]
        if faltan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{user.rol}' sin permiso para: {faltan}",
            )
        return user

    return _dep


def require_scopes(*required: str) -> Callable[..., Awaitable[CurrentUser]]:
    """Exige que el token contenga todos los scopes indicados."""

    required_set: Sequence[str] = required

    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        missing = [s for s in required_set if s not in user.scopes and s != user.rol]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Faltan scopes: {missing}",
            )
        return user

    return _dep
