"""Endpoints REST de dashboards (Smart Office, Big Data, informe mensual)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_permiso, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.common import SerieDiaria
from nijar_dti.schemas.dashboards import (
    BigDataOverview,
    ConsumoIAResumen,
    EnvironmentSeries,
    MonthlyReport,
    SmartOfficeOverview,
    TotemsHealthOverview,
    TotemUsageStats,
)
from nijar_dti.services import consumo_ia_service
from nijar_dti.services import dashboards_service as svc

router = APIRouter()

# Los dashboards Smart Office / Big Data / tótems forman parte del módulo DTI.
_ver_dti = require_permiso("ver_dti")


@router.get(
    "/ia/consumo",
    response_model=ConsumoIAResumen,
    summary="Consumo de IA generativa (tokens y coste estimado)",
)
async def consumo_ia(
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "analista_datos", "auditor"))
    ],
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ConsumoIAResumen:
    """Agregado del consumo de modelos de IA en todos los puntos de uso."""
    return await consumo_ia_service.resumen(db, desde=desde, hasta=hasta)


@router.get(
    "/smart-office/overview",
    response_model=SmartOfficeOverview,
    summary="Vista general Smart Office",
)
async def smart_office_overview(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_dti),
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
    user: CurrentUser = Depends(_ver_dti),
) -> EnvironmentSeries:
    return await svc.environment_series(db, desde, hasta, granularidad)


@router.get(
    "/big-data/overview",
    response_model=BigDataOverview,
    summary="Vista general Big Data turístico",
)
async def big_data_overview(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_dti),
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
    user: CurrentUser = Depends(_ver_dti),
) -> TotemUsageStats:
    return await svc.totems_usage(db, desde, hasta)


@router.get(
    "/totems/usage/series",
    response_model=SerieDiaria,
    summary="Serie diaria de interacciones de los tótems",
)
async def totems_usage_series(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_dti),
) -> SerieDiaria:
    return await svc.totems_usage_series(db, desde, hasta)


@router.get(
    "/totems/health",
    response_model=TotemsHealthOverview,
    summary="Salud y disponibilidad de los tótems",
)
async def totems_health(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_dti),
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
    user: Annotated[
        CurrentUser, Depends(require_roles("administrador_tic", "analista_datos", "auditor"))
    ] = ...,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
) -> MonthlyReport:
    return await svc.informe_mensual(db, year, month)
