"""Endpoints de noticias del Ayuntamiento de Níjar (Strapi, solo lectura).

La web municipal publica sus noticias en Strapi con un JSON público. La
plataforma las reexpone normalizadas para el tótem, el panel y el chatbot. Son
información pública, por lo que los listados no requieren autenticación (igual
que ``/gemelo/aire/resumen``). Si la fuente no está configurada, responde 503.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.connectors.noticias import NoticiasError
from nijar_dti.core.database import get_db
from nijar_dti.schemas.noticias import (
    CategoriasNoticiasOut,
    EstadoNoticias,
    NoticiaOut,
    NoticiasPageOut,
)
from nijar_dti.services import noticias_service as svc
from nijar_dti.services import traduccion_service

_LANG = Query(None, description="Idioma del tótem: en/de/fr se traducen (con caché)")


async def _traducida(
    db: AsyncSession, pagina: NoticiasPageOut, lang: str | None
) -> NoticiasPageOut:
    items = await traduccion_service.traducir_noticias(db, pagina.items, lang)
    return pagina if items is pagina.items else pagina.model_copy(update={"items": items})


router = APIRouter()


def _requiere_fuente() -> None:
    if not svc.noticias_configurado():
        raise HTTPException(
            status_code=503,
            detail="Fuente de noticias sin configurar (NOTICIAS_STRAPI_BASE_URL/PROJECT_ID)",
        )


@router.get("/estado", response_model=EstadoNoticias, summary="Estado de la fuente de noticias")
async def estado() -> EstadoNoticias:
    return svc.estado_noticias()


@router.get("", response_model=NoticiasPageOut, summary="Listado de noticias del Ayuntamiento")
async def listar(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    categoria: str | None = Query(None, description="documentId de la categoría"),
    buscar: str | None = Query(None, description="Búsqueda por título ($contains)"),
    lang: str | None = _LANG,
    db: AsyncSession = Depends(get_db),
) -> NoticiasPageOut:
    _requiere_fuente()
    try:
        if not categoria and not buscar:
            # Listado general (tótem y panel): con respaldo del último listado bueno
            pagina = await svc.listar_todas(page=page, page_size=page_size)
        else:
            pagina = await svc.listar_noticias(
                page=page, page_size=page_size, categoria_document_id=categoria, buscar=buscar
            )
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return await _traducida(db, pagina, lang)


@router.get("/turismo", response_model=NoticiasPageOut, summary="Noticias de la categoría Turismo")
async def turismo(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    lang: str | None = _LANG,
    db: AsyncSession = Depends(get_db),
) -> NoticiasPageOut:
    _requiere_fuente()
    try:
        pagina = await svc.listar_turismo(page=page, page_size=page_size)
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return await _traducida(db, pagina, lang)


@router.get(
    "/agenda",
    response_model=NoticiasPageOut,
    summary="Agenda cultural (noticias de la categoría Cultura de la web municipal)",
)
async def agenda(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    lang: str | None = _LANG,
    db: AsyncSession = Depends(get_db),
) -> NoticiasPageOut:
    _requiere_fuente()
    try:
        pagina = await svc.listar_agenda(page=page, page_size=page_size)
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return await _traducida(db, pagina, lang)


@router.get("/categorias", response_model=CategoriasNoticiasOut, summary="Categorías de noticias")
async def categorias() -> CategoriasNoticiasOut:
    _requiere_fuente()
    try:
        return await svc.listar_categorias()
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{slug}", response_model=NoticiaOut, summary="Noticia por slug (detalle)")
async def detalle(
    slug: str, lang: str | None = _LANG, db: AsyncSession = Depends(get_db)
) -> NoticiaOut:
    _requiere_fuente()
    try:
        noticia = await svc.noticia_por_slug(slug)
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if noticia is None:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return (await traduccion_service.traducir_noticias(db, [noticia], lang))[0]
