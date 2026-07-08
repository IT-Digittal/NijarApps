"""Esquemas Pydantic para autenticación."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUser(BaseModel):
    """Usuario autenticado obtenido del token JWT."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre_completo: str
    rol: str
    scopes: list[str] = Field(default_factory=list)
    permisos: list[str] = Field(default_factory=list)
    activo: bool = True
