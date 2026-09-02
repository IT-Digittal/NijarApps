"""Esquemas de las capas geográficas del gemelo 2D (catálogo + GeoJSON)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CapaGeograficaOut(BaseModel):
    """Entrada del catálogo de capas para el control del mapa."""

    id: UUID
    codigo: str
    nombre: str
    grupo: str
    tipo_geometria: str
    descripcion: str | None = None
    color: str
    color_borde: str
    opacidad: float
    campo_etiqueta: str | None = None
    orden: int
    activa: bool
    fuente: str | None = None
    n_elementos: int = 0

    model_config = ConfigDict(from_attributes=True)


class CapaGeograficaUpdate(BaseModel):
    """Cambios editables de una capa desde el panel (estilo y visibilidad).

    La geometría no se edita por aquí: se carga o reemplaza desde fichero con
    el comando ``python -m nijar_dti.data.cargar_capa``.
    """

    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
    color_borde: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
    opacidad: float | None = Field(default=None, ge=0.0, le=1.0)
    campo_etiqueta: str | None = Field(default=None, max_length=80)
    orden: int | None = Field(default=None, ge=0, le=999)
    activa: bool | None = None
    fuente: str | None = Field(default=None, max_length=255)


class GeoJSONFeature(BaseModel):
    """Rasgo GeoJSON estándar (RFC 7946)."""

    type: str = Field(default="Feature", pattern=r"^Feature$")
    id: str | None = None
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    """Colección GeoJSON de una capa, con su estilo por defecto embebido."""

    type: str = Field(default="FeatureCollection", pattern=r"^FeatureCollection$")
    capa: CapaGeograficaOut
    features: list[GeoJSONFeature]


class ParcelaCatastralOut(BaseModel):
    """Elemento catastral que contiene un punto (consulta punto-en-parcela)."""

    referencia_catastral: str | None = None
    nombre: str
    capa: str
    propiedades: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] | None = None
