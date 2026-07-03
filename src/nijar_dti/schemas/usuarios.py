"""Esquemas Pydantic para gestión de usuarios del CMS."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from nijar_dti.models.usuario import RolUsuario


class UsuarioResponse(BaseModel):
    """Datos públicos de un usuario para listados y ficha."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre_completo: str
    rol: RolUsuario
    activo: bool
    requiere_2fa: bool
    created_at: datetime
    updated_at: datetime


class UsuarioInviteRequest(BaseModel):
    """Payload para invitar (crear) un usuario desde el CMS."""

    email: EmailStr
    nombre_completo: str = Field(..., min_length=2, max_length=255)
    rol: RolUsuario
