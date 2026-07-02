"""Endpoints REST de dashboards (Smart Office, Big Data, informe mensual)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.dashboards import (
    BigDataOverview,
    EnvironmentSeries,
    MonthlyReport,
    SmartOfficeOverview,
    TotemsHealthOverview,
    TotemUsageStats,
)
from nijar_dti.services import dashboards_service as svc

router = APIRouter()


@router.get(
    "/smart-office/overview",
    response_model=SmartOfficeOverview,
    summary="Vista general Smart Office",
)
async def smart_office_overview(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> SmartOfficeOverview:
    return await svc.smart_office_overview(db)


@router.get(
    "/smart-office/environment",
    response_model=EnvironmentSeries,
    summary="Series ambientales (CO₂, temperatura, humedad, ruido)",
)
async def environment(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    granularidad: str = Query("hora", pattern=r"^(minuto|hora|dia)$"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> EnvironmentSeries:
    return await svc.environment_series(db, desde, hasta, granularidad)


@router.get(
    "/big-data/overview",
    response_model=BigDataOverview,
    summary="Vista general Big Data turístico",
)
async def big_data_overview(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> BigDataOverview:
    return await svc.big_data_overview(db)


@router.get(
    "/totems/usage",
    response_model=TotemUsageStats,
    summary="Estadísticas de uso de los tótems",
)
async def totems_usage(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> TotemUsageStats:
    return await svc.totems_usage(db, desde, hasta)


@router.get(
    "/totems/health",
    response_model=TotemsHealthOverview,
    summary="Salud y disponibilidad de los tótems",
)
async def totems_health(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> TotemsHealthOverview:
    return await svc.totems_health(db)


@router.get(
    "/reports/monthly",
    response_model=MonthlyReport,
    summary="Datos del informe mensual de servicio (C.1)",
)
async def monthly_report(
    year: int = Query(..., ge=2025, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: Annotated[CurrentUser, Depends(require_roles("administrador_tic", "analista_datos", "auditor"))] = ...,
    db: AsyncSession = Depends(get_db),
) -> MonthlyReport:
    return await svc.informe_mensual(db, year, month)
