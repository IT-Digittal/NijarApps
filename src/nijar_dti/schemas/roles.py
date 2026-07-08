"""Esquemas Pydantic para gestión de roles y permisos."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RolResponse(BaseModel):
    """Rol con su conjunto de permisos y metadatos para el panel."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    display: str
    descripcion: str | None = None
    permisos: list[str] = Field(default_factory=list)
    es_sistema: bool = False
    n_usuarios: int = 0


class RolCreateRequest(BaseModel):
    """Payload para crear un rol nuevo."""

    slug: str = Field(..., pattern=r"^[a-z][a-z0-9_]{1,49}$")
    display: str = Field(..., min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=255)
    permisos: list[str] = Field(default_factory=list)


class RolUpdateRequest(BaseModel):
    """Payload para editar un rol (campos opcionales)."""

    display: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=255)
    permisos: list[str] | None = None
