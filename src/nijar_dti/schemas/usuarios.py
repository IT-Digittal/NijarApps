"""Esquemas Pydantic para gestión de usuarios del CMS."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Nota: `rol` es un slug de texto libre (no el enum `RolUsuario`), porque los
# roles ahora se gestionan en base de datos y el administrador puede crear
# roles personalizados. La validación de que el slug existe se hace en servicio.


class UsuarioResponse(BaseModel):
    """Datos públicos de un usuario para listados y ficha."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre_completo: str
    rol: str
    activo: bool
    requiere_2fa: bool
    created_at: datetime
    updated_at: datetime


class UsuarioInviteRequest(BaseModel):
    """Payload para invitar (crear) un usuario desde el CMS."""

    email: EmailStr
    nombre_completo: str = Field(..., min_length=2, max_length=255)
    rol: str = Field(..., min_length=2, max_length=50)


class UsuarioUpdateRequest(BaseModel):
    """Payload para editar un usuario existente (campos opcionales)."""

    nombre_completo: str | None = Field(default=None, min_length=2, max_length=255)
    rol: str | None = Field(default=None, min_length=2, max_length=50)
    activo: bool | None = None


class PasswordTemporalResponse(BaseModel):
    """Respuesta al restablecer la contraseña de un usuario."""

    id: UUID
    email: EmailStr
    password_temporal: str
    mensaje: str = "Contraseña temporal generada. El usuario deberá cambiarla en el primer acceso."


class ModuloPermiso(BaseModel):
    """Un módulo/permiso del catálogo de la matriz."""

    id: str
    nombre: str
    grupo: str


class RolPermisos(BaseModel):
    """Permisos concedidos a un rol, con su nombre legible."""

    rol: str
    display: str
    permisos: list[str]
    es_sistema: bool = False
    n_usuarios: int = 0


class MatrizPermisos(BaseModel):
    """Matriz curada roles × módulos para el panel de administración."""

    modulos: list[ModuloPermiso]
    roles: list[RolPermisos]
