"""Endpoints de las verticales Smart City (alumbrado, agua, residuos,
movilidad, seguridad y energía)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.core.export import csv_response
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.verticales import (
    AguaOverview,
    AlumbradoOverview,
    CamaraCCTVOut,
    ContenedoresPage,
    CuadroMandoOut,
    EnergiaOverview,
    LuminariasPage,
    MovilidadOverview,
    PuntoMovilidadOut,
    ResiduosOverview,
    SectorAguaOut,
    SeguridadOverview,
    SuministrosPage,
    ZonaAlumbradoOut,
)
from nijar_dti.services import verticales_service as svc

router = APIRouter()


# --------------------------------------------------------------- ALUMBRADO
@router.get(
    "/alumbrado/overview",
    response_model=AlumbradoOverview,
    summary="KPIs del alumbrado",
)
async def alumbrado_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> AlumbradoOverview:
    return await svc.alumbrado_overview(db)


@router.get(
    "/alumbrado/zonas",
    response_model=list[ZonaAlumbradoOut],
    summary="Zonas de alumbrado",
)
async def alumbrado_zonas(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[ZonaAlumbradoOut]:
    return await svc.alumbrado_zonas(db)


@router.get(
    "/alumbrado/cuadros",
    response_model=list[CuadroMandoOut],
    summary="Cuadros de mando",
)
async def alumbrado_cuadros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[CuadroMandoOut]:
    return await svc.alumbrado_cuadros(db)


@router.get(
    "/alumbrado/luminarias",
    response_model=LuminariasPage,
    summary="Inventario de luminarias",
)
async def alumbrado_luminarias(
    zona: str | None = Query(None),
    estado: str | None = Query(None),
    tecnologia: str | None = Query(None),
    buscar: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> LuminariasPage:
    return await svc.alumbrado_luminarias(db, zona, estado, tecnologia, buscar, page, page_size)


# -------------------------------------------------------------------- AGUA
@router.get(
    "/agua/overview",
    response_model=AguaOverview,
    summary="KPIs del ciclo del agua",
)
async def agua_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> AguaOverview:
    return await svc.agua_overview(db)


@router.get(
    "/agua/sectores",
    response_model=list[SectorAguaOut],
    summary="Sectores hidráulicos",
)
async def agua_sectores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[SectorAguaOut]:
    return await svc.agua_sectores(db)


# ---------------------------------------------------------------- RESIDUOS
@router.get(
    "/residuos/overview",
    response_model=ResiduosOverview,
    summary="KPIs de residuos",
)
async def residuos_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> ResiduosOverview:
    return await svc.residuos_overview(db)


@router.get(
    "/residuos/contenedores",
    response_model=ContenedoresPage,
    summary="Contenedores",
)
async def residuos_contenedores(
    zona: str | None = Query(None),
    fraccion: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ContenedoresPage:
    return await svc.residuos_contenedores(db, zona, fraccion, page, page_size)


# --------------------------------------------------------------- MOVILIDAD
@router.get(
    "/movilidad/overview",
    response_model=MovilidadOverview,
    summary="KPIs de movilidad",
)
async def movilidad_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> MovilidadOverview:
    return await svc.movilidad_overview(db)


@router.get(
    "/movilidad/puntos",
    response_model=list[PuntoMovilidadOut],
    summary="Puntos de movilidad",
)
async def movilidad_puntos(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[PuntoMovilidadOut]:
    return await svc.movilidad_puntos(db)


# --------------------------------------------------------------- SEGURIDAD
@router.get(
    "/seguridad/overview",
    response_model=SeguridadOverview,
    summary="KPIs de seguridad",
)
async def seguridad_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> SeguridadOverview:
    return await svc.seguridad_overview(db)


@router.get(
    "/seguridad/camaras",
    response_model=list[CamaraCCTVOut],
    summary="Cámaras CCTV",
)
async def seguridad_camaras(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[CamaraCCTVOut]:
    return await svc.seguridad_camaras(db)


# ----------------------------------------------------------------- ENERGÍA
@router.get(
    "/energia/overview",
    response_model=EnergiaOverview,
    summary="KPIs de energía municipal",
)
async def energia_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> EnergiaOverview:
    return await svc.energia_overview(db)


@router.get(
    "/energia/suministros",
    response_model=SuministrosPage,
    summary="Suministros (CUPS)",
)
async def energia_suministros(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> SuministrosPage:
    return await svc.energia_suministros(db, page, page_size)


# --------------------------- Exportaciones CSV (bloque 11 del pliego) ---------------------------
@router.get("/alumbrado/luminarias.csv", summary="Exportar inventario de luminarias (CSV)")
async def export_luminarias(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    page = await svc.alumbrado_luminarias(db, page=1, page_size=100000)
    return csv_response(page.items, "alumbrado_luminarias_nijar")


@router.get("/alumbrado/cuadros.csv", summary="Exportar cuadros de mando (CSV)")
async def export_cuadros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return csv_response(await svc.alumbrado_cuadros(db), "alumbrado_cuadros_nijar")


@router.get("/agua/sectores.csv", summary="Exportar sectores de agua (CSV)")
async def export_sectores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return csv_response(await svc.agua_sectores(db), "agua_sectores_nijar")


@router.get("/residuos/contenedores.csv", summary="Exportar contenedores (CSV)")
async def export_contenedores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    page = await svc.residuos_contenedores(db, page=1, page_size=100000)
    return csv_response(page.items, "residuos_contenedores_nijar")


@router.get("/movilidad/puntos.csv", summary="Exportar puntos de movilidad (CSV)")
async def export_movilidad(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return csv_response(await svc.movilidad_puntos(db), "movilidad_puntos_nijar")


@router.get("/seguridad/camaras.csv", summary="Exportar cámaras CCTV (CSV)")
async def export_camaras(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    return csv_response(await svc.seguridad_camaras(db), "seguridad_camaras_nijar")


@router.get("/energia/suministros.csv", summary="Exportar suministros CUPS (CSV)")
async def export_suministros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    page = await svc.energia_suministros(db, page=1, page_size=100000)
    return csv_response(page.items, "energia_suministros_nijar")
