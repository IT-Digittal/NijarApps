"""Endpoints REST de ingesta IoT y consulta de sensores y observaciones."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.common import PageParams, Paginated
from nijar_dti.schemas.iot import (
    IngestResponse,
    ObservacionIn,
    ObservacionOut,
    SensorOut,
)
from nijar_dti.services import iot_service as svc

router = APIRouter()


def _page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def _obs_to_out(o) -> ObservacionOut:
    return ObservacionOut(
        id=o.id,
        sensor_id=o.sensor_id,
        observado_en=o.observado_en,
        valor=float(o.valor) if o.valor is not None else None,
        valores=o.valores,
        unidades=o.unidades,
        valido=o.valido,
        motivo_invalidez=o.motivo_invalidez,
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingerir una observación IoT por HTTP",
)
async def ingest(
    payload: ObservacionIn,
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "operador_smart_office"))
    ],
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    try:
        return await svc.ingerir_observacion(db, payload)
    except svc.SensorNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/sensors",
    response_model=Paginated[SensorOut],
    summary="Listar sensores del catálogo",
)
async def list_sensors(
    tipo: str | None = Query(None),
    estado: str | None = Query(None),
    page: PageParams = Depends(_page_params),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Paginated[SensorOut]:
    rows, total = await svc.listar_sensores(db, tipo, estado, page)
    items = [await svc.sensor_to_out(db, s) for s in rows]
    return Paginated[SensorOut].build(items, total, page)


@router.get(
    "/sensors/{sensor_id}/observations",
    response_model=list[ObservacionOut],
    summary="Histórico de observaciones de un sensor",
)
async def list_observations(
    sensor_id: UUID,
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=10_000),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ObservacionOut]:
    try:
        rows = await svc.historico_observaciones(db, sensor_id, desde, hasta, limit)
    except svc.SensorNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_obs_to_out(o) for o in rows]
