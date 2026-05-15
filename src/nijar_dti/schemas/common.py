"""Esquemas Pydantic comunes a todas las áreas funcionales."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIError(BaseModel):
    """Estructura estándar de error de la API."""

    code: str
    message: str
    details: dict | None = None


class GeoPoint(BaseModel):
    """Punto GeoJSON en WGS84."""

    type: str = Field(default="Point", pattern=r"^Point$")
    coordinates: list[float] = Field(..., min_length=2, max_length=2)

    model_config = ConfigDict(json_schema_extra={
        "example": {"type": "Point", "coordinates": [-2.139, 36.752]}
    })


class I18nText(BaseModel):
    """Texto multilingüe en los 4 idiomas obligatorios."""

    es: str | None = None
    en: str | None = None
    de: str | None = None
    fr: str | None = None


class TimestampedModel(BaseModel):
    """Mixin de timestamps de auditoría."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    """Parámetros estándar de paginación."""

    page: Annotated[int, Field(ge=1, le=1_000_000)] = 1
    page_size: Annotated[int, Field(ge=1, le=200)] = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Paginated(BaseModel, Generic[T]):
    """Respuesta paginada estándar."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Paginated[T]":
        return cls(items=items, total=total, page=params.page, page_size=params.page_size)


class IdResponse(BaseModel):
    """Respuesta simple con un identificador."""

    id: UUID
