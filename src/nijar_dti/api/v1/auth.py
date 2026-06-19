"""Endpoints de autenticación (OAuth2 + JWT, ENS Medio)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import (
    CurrentUser,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from nijar_dti.services import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión y obtener tokens JWT")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        user = await auth_service.authenticate(db, payload.email, payload.password)
    except auth_service.AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(**auth_service.issue_tokens(user))


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login OAuth2 (form-data: username=email, password)",
)
async def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login compatible con OAuth2 password flow (form-urlencoded).

    Acepta `username` (que se interpreta como email) y `password`. Útil para
    `curl -d 'username=...&password=...'` y para integraciones que esperan
    el flujo OAuth2 estándar. Devuelve el mismo `TokenResponse` que /login.
    """
    try:
        user = await auth_service.authenticate(db, form.username, form.password)
    except auth_service.AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(**auth_service.issue_tokens(user))


@router.post("/refresh", response_model=TokenResponse, summary="Refrescar token de acceso")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        tokens = await auth_service.refresh_tokens(db, payload.refresh_token)
    except auth_service.AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(**tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
async def logout(_: CurrentUser = Depends(get_current_user)) -> None:
    """Logout sin estado en servidor: el cliente descarta el token.

    Para revocación con blocklist se utiliza Redis con TTL = exp del token
    (implementación futura, fuera del Hito 1).
    """
    return None


@router.get("/me", response_model=CurrentUser, summary="Datos del usuario autenticado")
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
