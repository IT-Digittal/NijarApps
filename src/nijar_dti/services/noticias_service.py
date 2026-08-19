"""Servicio de noticias del Ayuntamiento (Strapi, solo lectura).

Capa fina sobre ``connectors.noticias.ClienteNoticiasStrapi`` que expone las
noticias municipales a los routers. No persiste nada: lee del origen bajo
demanda (como el gemelo digital).
"""

from __future__ import annotations

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.noticias import ClienteNoticiasStrapi
from nijar_dti.schemas.noticias import (
    CategoriaNoticiaOut,
    CategoriasNoticiasOut,
    EstadoNoticias,
    NoticiaOut,
    NoticiasPageOut,
)


def _cliente(settings: Settings | None = None) -> ClienteNoticiasStrapi:
    s = settings or get_settings()
    return ClienteNoticiasStrapi(
        base_url=s.noticias_strapi_base_url,
        project_id=s.noticias_strapi_project_id,
        timeout_seconds=s.noticias_timeout_seconds,
    )


def noticias_configurado(settings: Settings | None = None) -> bool:
    return _cliente(settings).is_configured


def estado_noticias(settings: Settings | None = None) -> EstadoNoticias:
    s = settings or get_settings()
    return EstadoNoticias(
        configurado=noticias_configurado(s),
        base_url=s.noticias_strapi_base_url,
        project_id=s.noticias_strapi_project_id,
    )


async def listar_noticias(
    *,
    page: int = 1,
    page_size: int = 12,
    categoria_document_id: str | None = None,
    buscar: str | None = None,
    settings: Settings | None = None,
) -> NoticiasPageOut:
    data = await _cliente(settings).listar(
        page=page,
        page_size=page_size,
        categoria_document_id=categoria_document_id,
        buscar=buscar,
    )
    return NoticiasPageOut(
        page=data["page"],
        page_size=data["page_size"],
        page_count=data["page_count"],
        total=data["total"],
        items=[NoticiaOut(**it) for it in data["items"]],
    )


async def listar_turismo(
    *, page: int = 1, page_size: int = 12, settings: Settings | None = None
) -> NoticiasPageOut:
    s = settings or get_settings()
    return await listar_noticias(
        page=page,
        page_size=page_size,
        categoria_document_id=s.noticias_categoria_turismo_id or None,
        settings=s,
    )


async def noticia_por_slug(slug: str, settings: Settings | None = None) -> NoticiaOut | None:
    art = await _cliente(settings).por_slug(slug)
    return NoticiaOut(**art) if art else None


async def listar_categorias(settings: Settings | None = None) -> CategoriasNoticiasOut:
    cats = await _cliente(settings).categorias()
    items = [CategoriaNoticiaOut(**c) for c in cats]
    return CategoriasNoticiasOut(total=len(items), categorias=items)
