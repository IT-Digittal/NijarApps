"""Endpoints de noticias del Ayuntamiento de Níjar (Strapi, solo lectura).

La web municipal publica sus noticias en Strapi con un JSON público. La
plataforma las reexpone normalizadas para el tótem, el panel y el chatbot. Son
información pública, por lo que los listados no requieren autenticación (igual
que ``/gemelo/aire/resumen``). Si la fuente no está configurada, responde 503.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from nijar_dti.connectors.noticias import NoticiasError
from nijar_dti.schemas.noticias import (
    CategoriasNoticiasOut,
    EstadoNoticias,
    NoticiaOut,
    NoticiasPageOut,
)
from nijar_dti.services import noticias_service as svc

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
) -> NoticiasPageOut:
    _requiere_fuente()
    try:
        return await svc.listar_noticias(
            page=page, page_size=page_size, categoria_document_id=categoria, buscar=buscar
        )
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/turismo", response_model=NoticiasPageOut, summary="Noticias de la categoría Turismo")
async def turismo(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
) -> NoticiasPageOut:
    _requiere_fuente()
    try:
        return await svc.listar_turismo(page=page, page_size=page_size)
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/categorias", response_model=CategoriasNoticiasOut, summary="Categorías de noticias"
)
async def categorias() -> CategoriasNoticiasOut:
    _requiere_fuente()
    try:
        return await svc.listar_categorias()
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{slug}", response_model=NoticiaOut, summary="Noticia por slug (detalle)")
async def detalle(slug: str) -> NoticiaOut:
    _requiere_fuente()
    try:
        noticia = await svc.noticia_por_slug(slug)
    except NoticiasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if noticia is None:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return noticia
