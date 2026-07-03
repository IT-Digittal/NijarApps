"""Endpoints del catálogo de fuentes de datos e integraciones.

Responde a la identificación de fuentes/APIs/servicios que deben conectarse
con la plataforma: qué datos genera nuestra solución (propias) y qué accesos
debe facilitar el Ayuntamiento (externas).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.core.export import csv_response
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.fuentes import FuenteDatoOut, FuentesResumen
from nijar_dti.services import fuentes_service as svc

router = APIRouter()

_ORIGEN = r"^(propia|externa)$"
_ESTADO = r"^(operativa|pendiente_desarrollo|pendiente_acceso|planificada)$"


@router.get("/fuentes", response_model=list[FuenteDatoOut], summary="Catálogo de fuentes de datos")
async def listar_fuentes(
    origen: str | None = Query(None, pattern=_ORIGEN),
    estado: str | None = Query(None, pattern=_ESTADO),
    categoria: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[FuenteDatoOut]:
    return await svc.listar_fuentes(db, origen, estado, categoria)


@router.get("/resumen", response_model=FuentesResumen, summary="Resumen del estado de integración")
async def resumen(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> FuentesResumen:
    return await svc.resumen_fuentes(db)


@router.get("/fuentes.csv", summary="Exportar el catálogo de fuentes (CSV)")
async def exportar_fuentes(
    origen: str | None = Query(None, pattern=_ORIGEN),
    estado: str | None = Query(None, pattern=_ESTADO),
    categoria: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    filas = await svc.listar_fuentes(db, origen, estado, categoria)
    return csv_response(filas, "fuentes_datos_nijar")
