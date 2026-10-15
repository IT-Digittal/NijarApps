"""Endpoints de las verticales Smart City (alumbrado, agua, residuos,
movilidad, seguridad y energía).

El acceso de lectura se controla por permiso de módulo (`ver_alumbrado`,
`ver_agua`, …): un rol restringido recibe 403 aunque llame directo a la API.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_permiso, require_roles
from nijar_dti.config import get_settings
from nijar_dti.connectors.datadis_fichero import FicheroDatadisError, leer_fichero
from nijar_dti.core.database import get_db
from nijar_dti.core.export import csv_response
from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia, EnergiaMunicipioDiario
from nijar_dti.models.verticales import SuministroEnergia
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.verticales import (
    AguaOverview,
    AlumbradoOverview,
    CamaraCCTVOut,
    ContenedoresPage,
    CuadroMandoOut,
    EnergiaMunicipioSerie,
    EnergiaOverview,
    EstadoDatadis,
    ImportacionDatadisOut,
    LecturaHorariaOut,
    LuminariasPage,
    MovilidadOverview,
    PuntoMovilidadOut,
    ResiduosOverview,
    SectorAguaOut,
    SeguridadOverview,
    SuministrosPage,
    ZonaAlumbradoOut,
)
from nijar_dti.services import datadis_service
from nijar_dti.services import verticales_service as svc

router = APIRouter()

# Guardas por permiso de módulo (una por vertical).
_ver_alumbrado = require_permiso("ver_alumbrado")
_ver_agua = require_permiso("ver_agua")
_ver_residuos = require_permiso("ver_residuos")
_ver_movilidad = require_permiso("ver_movilidad")
_ver_seguridad = require_permiso("ver_seguridad")
_ver_energia = require_permiso("ver_energia")
_importar_energia = require_roles("administrador_tic", "analista_datos")


# --------------------------------------------------------------- ALUMBRADO
@router.get(
    "/alumbrado/overview",
    response_model=AlumbradoOverview,
    summary="KPIs del alumbrado",
)
async def alumbrado_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_alumbrado)
) -> AlumbradoOverview:
    return await svc.alumbrado_overview(db)


@router.get(
    "/alumbrado/zonas",
    response_model=list[ZonaAlumbradoOut],
    summary="Zonas de alumbrado",
)
async def alumbrado_zonas(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_alumbrado)
) -> list[ZonaAlumbradoOut]:
    return await svc.alumbrado_zonas(db)


@router.get(
    "/alumbrado/cuadros",
    response_model=list[CuadroMandoOut],
    summary="Cuadros de mando",
)
async def alumbrado_cuadros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_alumbrado)
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
    user: CurrentUser = Depends(_ver_alumbrado),
) -> LuminariasPage:
    return await svc.alumbrado_luminarias(db, zona, estado, tecnologia, buscar, page, page_size)


# -------------------------------------------------------------------- AGUA
@router.get(
    "/agua/overview",
    response_model=AguaOverview,
    summary="KPIs del ciclo del agua",
)
async def agua_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_agua)
) -> AguaOverview:
    return await svc.agua_overview(db)


@router.get(
    "/agua/sectores",
    response_model=list[SectorAguaOut],
    summary="Sectores hidráulicos",
)
async def agua_sectores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_agua)
) -> list[SectorAguaOut]:
    return await svc.agua_sectores(db)


# ---------------------------------------------------------------- RESIDUOS
@router.get(
    "/residuos/overview",
    response_model=ResiduosOverview,
    summary="KPIs de residuos",
)
async def residuos_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_residuos)
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
    user: CurrentUser = Depends(_ver_residuos),
) -> ContenedoresPage:
    return await svc.residuos_contenedores(db, zona, fraccion, page, page_size)


# --------------------------------------------------------------- MOVILIDAD
@router.get(
    "/movilidad/overview",
    response_model=MovilidadOverview,
    summary="KPIs de movilidad",
)
async def movilidad_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_movilidad)
) -> MovilidadOverview:
    return await svc.movilidad_overview(db)


@router.get(
    "/movilidad/puntos",
    response_model=list[PuntoMovilidadOut],
    summary="Puntos de movilidad",
)
async def movilidad_puntos(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_movilidad)
) -> list[PuntoMovilidadOut]:
    return await svc.movilidad_puntos(db)


# --------------------------------------------------------------- SEGURIDAD
@router.get(
    "/seguridad/overview",
    response_model=SeguridadOverview,
    summary="KPIs de seguridad",
)
async def seguridad_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_seguridad)
) -> SeguridadOverview:
    return await svc.seguridad_overview(db)


@router.get(
    "/seguridad/camaras",
    response_model=list[CamaraCCTVOut],
    summary="Cámaras CCTV",
)
async def seguridad_camaras(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_seguridad)
) -> list[CamaraCCTVOut]:
    return await svc.seguridad_camaras(db)


# ----------------------------------------------------------------- ENERGÍA
@router.get(
    "/energia/overview",
    response_model=EnergiaOverview,
    summary="KPIs de energía municipal",
)
async def energia_overview(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_energia)
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
    user: CurrentUser = Depends(_ver_energia),
) -> SuministrosPage:
    return await svc.energia_suministros(db, page, page_size)


@router.get(
    "/energia/municipio",
    response_model=EnergiaMunicipioSerie,
    summary="Consumo eléctrico de todo el municipio por día y sector (Datadis)",
)
async def energia_municipio(
    dias: int = Query(30, ge=1, le=730, description="Últimos N días con datos"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_energia),
) -> EnergiaMunicipioSerie:
    hasta = (
        await db.execute(select(func.max(EnergiaMunicipioDiario.fecha)))
    ).scalar_one_or_none() or date.today()
    datos = await datadis_service.serie_municipio(db, hasta - timedelta(days=dias - 1), hasta)
    return EnergiaMunicipioSerie(**datos)


@router.get(
    "/energia/suministros/{cups}/curva",
    response_model=list[LecturaHorariaOut],
    summary="Curva de consumo horaria de un suministro municipal (Datadis)",
)
async def energia_curva(
    cups: str,
    dias: int = Query(7, ge=1, le=62),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_ver_energia),
) -> list[LecturaHorariaOut]:
    hasta = datetime.now(UTC)
    datos = await datadis_service.curva_suministro(db, cups, hasta - timedelta(days=dias), hasta)
    return [LecturaHorariaOut(**d) for d in datos]


@router.get(
    "/energia/datadis/estado",
    response_model=EstadoDatadis,
    summary="Estado de la integración con Datadis",
)
async def energia_datadis_estado(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_energia)
) -> EstadoDatadis:
    s = get_settings()
    ultima, dias = (
        await db.execute(
            select(
                func.max(EnergiaMunicipioDiario.fecha),
                func.count(func.distinct(EnergiaMunicipioDiario.fecha)),
            )
        )
    ).one()
    ultima_lectura = (
        await db.execute(select(func.max(ConsumoHorarioEnergia.momento)))
    ).scalar_one_or_none()
    reales = (
        await db.execute(
            select(func.count()).where(
                SuministroEnergia.metadatos["fuente"].as_string() == datadis_service.FUENTE
            )
        )
    ).scalar_one()
    return EstadoDatadis(
        publico_activo=s.datadis_publico_activo,
        privado_configurado=datadis_service.datadis_configurado(s),
        ultima_fecha_publica=ultima,
        dias_publicos_cargados=int(dias or 0),
        suministros_reales=int(reales or 0),
        ultima_lectura_privada=ultima_lectura,
    )


_MAX_FICHERO_DATADIS = 20 * 1024 * 1024


@router.post(
    "/energia/datadis/importar",
    response_model=ImportacionDatadisOut,
    summary="Importar el fichero descargado de datadis.es (Consumos y contratos)",
)
async def energia_datadis_importar(
    archivo: UploadFile = File(..., description="CSV o Excel descargado de datadis.es/queries"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(_importar_energia),
) -> ImportacionDatadisOut:
    """Carga manual mientras no hay usuario de Datadis para su API.

    Idempotente: volver a subir el mismo mes actualiza los valores.
    """
    contenido = await archivo.read(_MAX_FICHERO_DATADIS + 1)
    if len(contenido) > _MAX_FICHERO_DATADIS:
        raise HTTPException(413, "El fichero supera los 20 MB")
    try:
        registros = leer_fichero(contenido, archivo.filename or "")
    except FicheroDatadisError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — fichero corrupto o de otro tipo
        raise HTTPException(422, f"No se puede leer el fichero: {exc}") from exc
    cuenta = await datadis_service.guardar_registros(db, registros)
    fechas = [r.fecha for r in registros if r is not None]
    return ImportacionDatadisOut(
        fichero=archivo.filename or "fichero",
        desde=min(fechas) if fechas else None,
        hasta=max(fechas) if fechas else None,
        **cuenta,
    )


# --------------------------- Exportaciones CSV (bloque 11 del pliego) ---------------------------
@router.get("/alumbrado/luminarias.csv", summary="Exportar inventario de luminarias (CSV)")
async def export_luminarias(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_alumbrado)
):
    page = await svc.alumbrado_luminarias(db, page=1, page_size=100000)
    return csv_response(page.items, "alumbrado_luminarias_nijar")


@router.get("/alumbrado/cuadros.csv", summary="Exportar cuadros de mando (CSV)")
async def export_cuadros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_alumbrado)
):
    return csv_response(await svc.alumbrado_cuadros(db), "alumbrado_cuadros_nijar")


@router.get("/agua/sectores.csv", summary="Exportar sectores de agua (CSV)")
async def export_sectores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_agua)
):
    return csv_response(await svc.agua_sectores(db), "agua_sectores_nijar")


@router.get("/residuos/contenedores.csv", summary="Exportar contenedores (CSV)")
async def export_contenedores(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_residuos)
):
    page = await svc.residuos_contenedores(db, page=1, page_size=100000)
    return csv_response(page.items, "residuos_contenedores_nijar")


@router.get("/movilidad/puntos.csv", summary="Exportar puntos de movilidad (CSV)")
async def export_movilidad(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_movilidad)
):
    return csv_response(await svc.movilidad_puntos(db), "movilidad_puntos_nijar")


@router.get("/seguridad/camaras.csv", summary="Exportar cámaras CCTV (CSV)")
async def export_camaras(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_seguridad)
):
    return csv_response(await svc.seguridad_camaras(db), "seguridad_camaras_nijar")


@router.get("/energia/suministros.csv", summary="Exportar suministros CUPS (CSV)")
async def export_suministros(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(_ver_energia)
):
    page = await svc.energia_suministros(db, page=1, page_size=100000)
    return csv_response(page.items, "energia_suministros_nijar")
