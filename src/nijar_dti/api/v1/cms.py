"""Endpoints REST del CMS centralizado (publicación multicanal)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.cms import ContenidoIn, ContenidoOut
from nijar_dti.schemas.common import PageParams, Paginated
from nijar_dti.services import cms_service as svc

router = APIRouter()


def _page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def _to_out(c) -> ContenidoOut:
    return ContenidoOut(
        id=c.id,
        titulo=c.titulo,
        titulo_i18n=c.titulo_i18n,
        cuerpo=c.cuerpo,
        cuerpo_i18n=c.cuerpo_i18n,
        canales=list(c.canales) if c.canales else [],
        plantilla_id=c.plantilla_id,
        recurso_id=c.recurso_id,
        publicar_desde=c.publicar_desde,
        publicar_hasta=c.publicar_hasta,
        imagenes=c.imagenes,
        enlaces=c.enlaces,
        etiquetas=c.etiquetas,
        estado=str(c.estado.value if hasattr(c.estado, "value") else c.estado),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get(
    "/content",
    response_model=Paginated[ContenidoOut],
    summary="Listar contenidos publicables",
)
async def list_content(
    canal: str | None = Query(None, pattern=r"^(totem|web|app|todos)$"),
    idioma: str | None = Query(None, pattern=r"^(es|en|de|fr)$"),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Paginated[ContenidoOut]:
    rows, total = await svc.listar_contenidos(db, canal, idioma, page)
    return Paginated[ContenidoOut].build([_to_out(c) for c in rows], total, page)


@router.post(
    "/content",
    response_model=ContenidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo contenido",
)
async def create_content(
    payload: ContenidoIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> ContenidoOut:
    try:
        c = await svc.crear_contenido(db, payload, created_by=user.id)
    except svc.CMSValidation as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_out(c)


@router.get(
    "/content/{content_id}",
    response_model=ContenidoOut,
    summary="Detalle de un contenido",
)
async def get_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ContenidoOut:
    try:
        c = await svc.obtener_contenido(db, content_id)
    except svc.CMSNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_out(c)


@router.put(
    "/content/{content_id}",
    response_model=ContenidoOut,
    summary="Actualizar contenido",
)
async def update_content(
    content_id: UUID,
    payload: ContenidoIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> ContenidoOut:
    try:
        c = await svc.actualizar_contenido(db, content_id, payload, updated_by=user.id)
    except svc.CMSNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except svc.CMSValidation as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_out(c)


@router.delete(
    "/content/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Despublicar contenido (archivar)",
)
async def delete_content(
    content_id: UUID,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await svc.despublicar_contenido(db, content_id, updated_by=user.id)
    except svc.CMSNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/templates",
    response_model=list[dict],
    summary="Listar plantillas de contenido disponibles",
)
async def list_templates(
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    return svc.listar_plantillas()
