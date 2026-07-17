"""Esquemas CMS centralizado."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from nijar_dti.schemas.common import I18nText


CANALES_VALIDOS = {"totem", "web", "app"}


class ContenidoBase(BaseModel):
    titulo: str = Field(..., max_length=255)
    titulo_i18n: I18nText | None = None
    cuerpo: str
    cuerpo_i18n: I18nText | None = None
    canales: list[str] = Field(default_factory=list)
    plantilla_id: str | None = None
    recurso_id: UUID | None = None
    publicar_desde: datetime | None = None
    publicar_hasta: datetime | None = None
    imagenes: list[str] | None = None
    enlaces: dict | None = None
    etiquetas: list[str] | None = None


class ContenidoIn(ContenidoBase):
    publicar: bool = False


class ContenidoOut(ContenidoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado: str
    created_at: datetime
    updated_at: datetime


class AvisoPublicoOut(BaseModel):
    """Contenido publicado tal como lo consume el tótem (sin autenticación)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    titulo_i18n: I18nText | None = None
    cuerpo: str
    cuerpo_i18n: I18nText | None = None
    publicar_hasta: datetime | None = None
