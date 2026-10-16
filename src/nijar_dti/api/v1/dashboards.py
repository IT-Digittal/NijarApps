"""Endpoints REST de dashboards (Smart Office, Big Data, informe mensual)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_permiso, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.core.export import csv_response
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
from nijar_dti.schemas.interacciones import EventosTotemIn, InteraccionTotemOut, ListadoTotem
from nijar_dti.services import consumo_ia_service
from nijar_dti.services import dashboards_service as svc
from nijar_dti.services import interacciones_service as inter_svc

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


# ------------------- Interacciones con los contenidos del tótem -------------------


@router.post(
    "/totems/eventos",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Registrar lo que el visitante ve en el tótem (endpoint público)",
)
async def registrar_eventos_totem(
    lote: EventosTotemIn, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Lo llama el propio tótem (sin sesión de usuario) en lotes de hasta 50
    eventos: sección abierta, ficha consultada, noticia, mapa, QR mostrado,
    cambio de idioma, fin de sesión… Datos anónimos: solo la sesión del tótem."""
    return {"guardados": await inter_svc.registrar_eventos_totem(db, lote)}


def _filtros_totem(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None, description="Una fecha sin hora incluye el día"),
    totem: str | None = Query(None, pattern=r"^[a-z0-9_-]{1,40}$"),
    evento: str | None = Query(None, pattern=r"^[a-z_]{2,30}$"),
    seccion: str | None = Query(None, max_length=40),
    idioma: str | None = Query(None, pattern=r"^(es|en|de|fr)$"),
    q: str | None = Query(None, max_length=200, description="Texto en contenido o detalle"),
    sesion: str | None = Query(None, max_length=100),
    incluir_demo: bool = Query(False, description="Incluir los registros de demostración"),
) -> dict[str, object]:
    return {
        "desde": desde,
        "hasta": hasta,
        "totem": totem,
        "evento": evento,
        "seccion": seccion,
        "idioma": idioma,
        "q": q,
        "sesion": sesion,
        "incluir_demo": incluir_demo,
    }


_ORDEN_TOTEM = Query("reciente", pattern=r"^(reciente|antiguo)$")


@router.get(
    "/totems/interacciones",
    response_model=ListadoTotem,
    summary="Listado de interacciones con los contenidos del tótem (con filtros)",
)
async def listar_interacciones_totem(
    filtros: Annotated[dict[str, object], Depends(_filtros_totem)],
    user: Annotated[CurrentUser, Depends(_ver_dti)],
    page: int = Query(1, ge=1, le=100_000),
    page_size: int = Query(50, ge=1, le=200),
    orden: str = _ORDEN_TOTEM,
    db: AsyncSession = Depends(get_db),
) -> ListadoTotem:
    return await inter_svc.listar_totem(db, page=page, page_size=page_size, orden=orden, **filtros)


@router.get(
    "/totems/interacciones/export",
    summary="Exportar las interacciones del tótem filtradas a CSV (Excel)",
    response_class=Response,
)
async def exportar_interacciones_totem(
    filtros: Annotated[dict[str, object], Depends(_filtros_totem)],
    user: Annotated[CurrentUser, Depends(_ver_dti)],
    orden: str = _ORDEN_TOTEM,
    db: AsyncSession = Depends(get_db),
) -> Response:
    filas = await inter_svc.exportar_totem(db, orden=orden, **filtros)
    return csv_response(filas, "interacciones_totem", excel=True)


@router.get(
    "/totems/interacciones/sesion/{sesion}",
    response_model=list[InteraccionTotemOut],
    summary="Recorrido completo de una sesión en el tótem",
)
async def recorrido_sesion_totem(
    sesion: str,
    user: Annotated[CurrentUser, Depends(_ver_dti)],
    db: AsyncSession = Depends(get_db),
) -> list[InteraccionTotemOut]:
    return await inter_svc.recorrido_sesion(db, sesion)
