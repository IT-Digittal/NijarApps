"""Endpoints del ticketing de incidencias del mantenimiento (C.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.incidencias import (
    IncidenciaIn,
    IncidenciaOut,
    IncidenciaResolverIn,
    InformeANS,
)
from nijar_dti.services import incidencias_service as svc

router = APIRouter()

_GESTORES = ("administrador_tic", "operador_smart_office")


@router.post(
    "",
    response_model=IncidenciaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una incidencia o acción preventiva (C.1)",
)
async def crear(
    payload: IncidenciaIn,
    user: Annotated[CurrentUser, Depends(require_roles(*_GESTORES))],
    db: AsyncSession = Depends(get_db),
) -> IncidenciaOut:
    inc = await svc.crear_incidencia(db, payload)
    return IncidenciaOut.model_validate(inc)


@router.get(
    "",
    response_model=list[IncidenciaOut],
    summary="Listar incidencias",
)
async def listar(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    estado: str | None = Query(None, pattern=r"^(abierta|en_progreso|resuelta|cerrada)$"),
    severidad: str | None = Query(None, pattern=r"^(critica|alta|media|baja)$"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[IncidenciaOut]:
    filas = await svc.listar_incidencias(db, desde, hasta, estado, severidad)
    return [IncidenciaOut.model_validate(i) for i in filas]


@router.patch(
    "/{incidencia_id}/resolver",
    response_model=IncidenciaOut,
    summary="Marcar una incidencia como resuelta",
)
async def resolver(
    incidencia_id: UUID,
    payload: IncidenciaResolverIn,
    user: Annotated[CurrentUser, Depends(require_roles(*_GESTORES))],
    db: AsyncSession = Depends(get_db),
) -> IncidenciaOut:
    try:
        inc = await svc.resolver_incidencia(db, incidencia_id, payload)
    except svc.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidenciaOut.model_validate(inc)


@router.get(
    "/ans",
    response_model=InformeANS,
    summary="Cumplimiento ANS agregado de un periodo",
)
async def ans(
    desde: datetime = Query(...),
    hasta: datetime = Query(...),
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "auditor", "analista_datos"))
    ] = ...,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
) -> InformeANS:
    return await svc.informe_ans(db, desde, hasta)
