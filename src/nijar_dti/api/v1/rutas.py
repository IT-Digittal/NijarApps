"""Endpoints del planificador de rutas y recomendaciones (A.1 / B.2).

Canal público (sin autenticación): los consume el tótem y el chatbot para
proponer itinerarios y sugerir visitas y eventos a los visitantes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.database import get_db
from nijar_dti.schemas.rutas import (
    PlanificarRutaIn,
    RecomendacionesOut,
    RutaPlanificada,
)
from nijar_dti.services import rutas_service as svc

router = APIRouter()


@router.post(
    "/planificar",
    response_model=RutaPlanificada,
    summary="Planificar un itinerario de recursos turísticos desde un punto",
)
async def planificar(
    payload: PlanificarRutaIn, db: AsyncSession = Depends(get_db)
) -> RutaPlanificada:
    return await svc.planificar_ruta(db, payload)


@router.get(
    "/recomendaciones",
    response_model=RecomendacionesOut,
    summary="Proponer visitas y asistencia a eventos próximos",
)
async def recomendaciones(
    idioma: str = Query("es", pattern=r"^(es|en|de|fr)$"),
    dias: int = Query(30, ge=1, le=365),
    limite: int = Query(6, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> RecomendacionesOut:
    return await svc.recomendaciones(db, idioma, dias, limite)
