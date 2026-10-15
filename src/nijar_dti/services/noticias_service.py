"""Servicio de noticias del Ayuntamiento (Strapi, solo lectura).

Capa fina sobre ``connectors.noticias.ClienteNoticiasStrapi`` que expone las
noticias municipales a los routers. Lee del origen bajo demanda (siempre lo
último publicado) y guarda en memoria el último listado de Turismo correcto:
si Strapi falla o tarda, el tótem sigue mostrando las noticias más recientes
conocidas en lugar de quedarse vacío. ``refrescar_noticias_loop`` mantiene ese
listado al día en segundo plano y deja traza en los logs de cada carga.
"""

from __future__ import annotations

import asyncio

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.noticias import ClienteNoticiasStrapi, NoticiasError
from nijar_dti.core.logging import get_logger
from nijar_dti.schemas.noticias import (
    CategoriaNoticiaOut,
    CategoriasNoticiasOut,
    EstadoNoticias,
    NoticiaOut,
    NoticiasPageOut,
)

logger = get_logger(__name__)

# Último listado correcto por (fuente, page, page_size): "turismo" o "agenda"
_ultimo_listado: dict[tuple[str, int, int], NoticiasPageOut] = {}


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
    categoria_slug: str | None = None,
    buscar: str | None = None,
    settings: Settings | None = None,
) -> NoticiasPageOut:
    data = await _cliente(settings).listar(
        page=page,
        page_size=page_size,
        categoria_document_id=categoria_document_id,
        categoria_slug=categoria_slug,
        buscar=buscar,
    )
    return NoticiasPageOut(
        page=data["page"],
        page_size=data["page_size"],
        page_count=data["page_count"],
        total=data["total"],
        items=[NoticiaOut(**it) for it in data["items"]],
    )


async def _con_respaldo(
    fuente: str,
    page: int,
    page_size: int,
    settings: Settings,
    *,
    categoria_document_id: str | None = None,
    categoria_slug: str | None = None,
) -> NoticiasPageOut:
    """Lista del origen; ante un fallo devuelve el último listado bueno conocido."""
    clave = (fuente, page, page_size)
    try:
        res = await listar_noticias(
            page=page,
            page_size=page_size,
            categoria_document_id=categoria_document_id,
            categoria_slug=categoria_slug,
            settings=settings,
        )
    except NoticiasError as exc:
        previo = _ultimo_listado.get(clave)
        if previo is None:
            raise
        logger.warning(
            "Strapi no disponible: se sirve el último listado", fuente=fuente, error=str(exc)
        )
        return previo
    _ultimo_listado[clave] = res
    return res


async def listar_turismo(
    *, page: int = 1, page_size: int = 12, settings: Settings | None = None
) -> NoticiasPageOut:
    """Noticias de la categoría Turismo (sección Noticias del tótem)."""
    s = settings or get_settings()
    return await _con_respaldo(
        "turismo",
        page,
        page_size,
        s,
        categoria_document_id=s.noticias_categoria_turismo_id or None,
    )


async def listar_agenda(
    *, page: int = 1, page_size: int = 12, settings: Settings | None = None
) -> NoticiasPageOut:
    """Agenda cultural: noticias de la categoría «Cultura» de la web municipal."""
    s = settings or get_settings()
    return await _con_respaldo(
        "agenda",
        page,
        page_size,
        s,
        categoria_document_id=s.noticias_categoria_agenda_id or None,
        categoria_slug=s.noticias_categoria_agenda_slug or None,
    )


async def refrescar_noticias_loop(interval_seconds: int) -> None:
    """Recarga periódica de las noticias y la agenda cultural del tótem.

    Mantiene caliente el último listado correcto y deja en los logs la fecha
    de la publicación más reciente, para detectar si el origen deja de publicar.
    """
    while True:
        if noticias_configurado():
            for fuente, listar in (("turismo", listar_turismo), ("agenda", listar_agenda)):
                try:
                    res = await listar(page=1, page_size=12)
                    reciente = res.items[0].publicado_en if res.items else None
                    logger.info(
                        "Contenidos del tótem actualizados",
                        fuente=fuente,
                        total=res.total,
                        mas_reciente=reciente,
                    )
                except NoticiasError as exc:
                    logger.warning(
                        "No se pudieron actualizar los contenidos", fuente=fuente, error=str(exc)
                    )
                except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
                    logger.error("Error inesperado actualizando contenidos", error=str(exc))
        await asyncio.sleep(interval_seconds)


async def noticia_por_slug(slug: str, settings: Settings | None = None) -> NoticiaOut | None:
    art = await _cliente(settings).por_slug(slug)
    return NoticiaOut(**art) if art else None


async def listar_categorias(settings: Settings | None = None) -> CategoriasNoticiasOut:
    cats = await _cliente(settings).categorias()
    items = [CategoriaNoticiaOut(**c) for c in cats]
    return CategoriasNoticiasOut(total=len(items), categorias=items)
