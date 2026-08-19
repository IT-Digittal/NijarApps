"""Esquemas de las noticias del Ayuntamiento (Strapi, solo lectura)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class EstadoNoticias(BaseModel):
    """Estado de configuración de la fuente de noticias."""

    configurado: bool
    base_url: str
    project_id: str


class NoticiaOut(BaseModel):
    """Noticia normalizada del Ayuntamiento."""

    id: int | None = None
    document_id: str
    titulo: str
    descripcion: str | None = None
    slug: str
    contenido: str | None = None  # solo en el detalle por slug
    fecha: date | None = None
    publicado_en: datetime | None = None
    imagen_url: str | None = None
    categorias: list[str] = []


class NoticiasPageOut(BaseModel):
    """Página de noticias con metadatos de paginación."""

    fuente: str = "strapi"
    page: int
    page_size: int
    page_count: int
    total: int
    items: list[NoticiaOut]


class CategoriaNoticiaOut(BaseModel):
    document_id: str
    nombre: str
    slug: str


class CategoriasNoticiasOut(BaseModel):
    total: int
    categorias: list[CategoriaNoticiaOut]
