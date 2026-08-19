"""Endpoints REST de recursos turísticos, eventos y servicios."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.common import PageParams, Paginated
from nijar_dti.schemas.tourism import (
    EventoFilter,
    EventoTuristicoIn,
    EventoTuristicoOut,
    RecursoTuristicoFilter,
    RecursoTuristicoIn,
    RecursoTuristicoOut,
    ServicioFilter,
    ServicioIn,
    ServicioOut,
)
from nijar_dti.services import tourism_service as svc

router = APIRouter()


# -------- helpers --------


def _page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


# =====================================================
#                 RECURSOS TURÍSTICOS
# =====================================================


@router.get(
    "/resources",
    response_model=Paginated[RecursoTuristicoOut],
    summary="Listar recursos turísticos",
)
async def list_resources(
    categoria: str | None = Query(None),
    municipio: str | None = Query(None),
    publicado: bool | None = Query(None),
    cerca_de_lat: float | None = Query(None, ge=-90, le=90),
    cerca_de_lon: float | None = Query(None, ge=-180, le=180),
    radio_metros: int | None = Query(None, ge=1, le=100_000),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
) -> Paginated[RecursoTuristicoOut]:
    filtros = RecursoTuristicoFilter(
        categoria=categoria,
        municipio=municipio,
        publicado=publicado,
        cerca_de_lat=cerca_de_lat,
        cerca_de_lon=cerca_de_lon,
        radio_metros=radio_metros,
    )
    rows, total = await svc.listar_recursos(db, filtros, page)
    items = [await svc.recurso_to_out(db, r) for r in rows]
    return Paginated[RecursoTuristicoOut].build(items, total, page)


@router.get(
    "/resources/{resource_id}",
    response_model=RecursoTuristicoOut,
    summary="Detalle de un recurso turístico",
)
async def get_resource(
    resource_id: UUID, db: AsyncSession = Depends(get_db)
) -> RecursoTuristicoOut:
    try:
        r = await svc.obtener_recurso(db, resource_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await svc.recurso_to_out(db, r)


@router.post(
    "/resources",
    response_model=RecursoTuristicoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un recurso turístico",
)
async def create_resource(
    payload: RecursoTuristicoIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> RecursoTuristicoOut:
    try:
        r = await svc.crear_recurso(db, payload, created_by=user.id)
    except svc.Conflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await svc.recurso_to_out(db, r)


@router.put(
    "/resources/{resource_id}",
    response_model=RecursoTuristicoOut,
    summary="Actualizar un recurso turístico",
)
async def update_resource(
    resource_id: UUID,
    payload: RecursoTuristicoIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> RecursoTuristicoOut:
    try:
        r = await svc.actualizar_recurso(db, resource_id, payload, updated_by=user.id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await svc.recurso_to_out(db, r)


@router.delete(
    "/resources/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Despublicar un recurso (soft delete)",
)
async def delete_resource(
    resource_id: UUID,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await svc.eliminar_recurso(db, resource_id, deleted_by=user.id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# =====================================================
#                       EVENTOS
# =====================================================


@router.get(
    "/events",
    response_model=Paginated[EventoTuristicoOut],
    summary="Listar eventos turísticos",
)
async def list_events(
    desde: str | None = Query(None, description="ISO 8601"),
    hasta: str | None = Query(None, description="ISO 8601"),
    tipo: str | None = Query(None),
    publicado: bool | None = Query(None),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
) -> Paginated[EventoTuristicoOut]:
    from datetime import datetime

    filtros = EventoFilter(
        desde=datetime.fromisoformat(desde) if desde else None,
        hasta=datetime.fromisoformat(hasta) if hasta else None,
        tipo=tipo,
        publicado=publicado,
    )
    rows, total = await svc.listar_eventos(db, filtros, page)
    items = [await svc.evento_to_out(db, e) for e in rows]
    return Paginated[EventoTuristicoOut].build(items, total, page)


@router.get(
    "/events/{event_id}",
    response_model=EventoTuristicoOut,
    summary="Detalle de un evento",
)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_db)) -> EventoTuristicoOut:
    try:
        e = await svc.obtener_evento(db, event_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await svc.evento_to_out(db, e)


@router.post(
    "/events",
    response_model=EventoTuristicoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear evento turístico",
)
async def create_event(
    payload: EventoTuristicoIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> EventoTuristicoOut:
    try:
        e = await svc.crear_evento(db, payload, created_by=user.id)
    except svc.Conflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await svc.evento_to_out(db, e)


# =====================================================
#                       SERVICIOS
# =====================================================


@router.get(
    "/services",
    response_model=Paginated[ServicioOut],
    summary="Listar servicios turísticos",
)
async def list_services(
    tipo: str | None = Query(None),
    municipio: str | None = Query(None),
    publicado: bool | None = Query(None),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
) -> Paginated[ServicioOut]:
    filtros = ServicioFilter(tipo=tipo, municipio=municipio, publicado=publicado)
    rows, total = await svc.listar_servicios(db, filtros, page)
    items = [await svc.servicio_to_out(db, s) for s in rows]
    return Paginated[ServicioOut].build(items, total, page)


@router.get(
    "/services/{service_id}",
    response_model=ServicioOut,
    summary="Detalle de un servicio",
)
async def get_service(service_id: UUID, db: AsyncSession = Depends(get_db)) -> ServicioOut:
    try:
        s = await svc.obtener_servicio(db, service_id)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await svc.servicio_to_out(db, s)


@router.post(
    "/services",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear servicio turístico",
)
async def create_service(
    payload: ServicioIn,
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "gestor_contenidos"))],
    db: AsyncSession = Depends(get_db),
) -> ServicioOut:
    try:
        s = await svc.crear_servicio(db, payload, created_by=user.id)
    except svc.Conflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return await svc.servicio_to_out(db, s)
