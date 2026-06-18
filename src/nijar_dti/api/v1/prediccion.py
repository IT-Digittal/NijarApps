"""Endpoints de modelos predictivos de afluencia (A.2 / A.3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.prediccion import (
    DeteccionAnomalias,
    PrediccionAfluencia,
    ValidacionModelo,
)
from nijar_dti.services import prediccion_service as svc
from nijar_dti.services.prediccion_service import METRICAS_VALIDAS

router = APIRouter()


def _validar_metrica(metrica: str) -> str:
    if metrica not in METRICAS_VALIDAS:
        raise HTTPException(
            status_code=422,
            detail=f"Métrica '{metrica}' no soportada. Válidas: {', '.join(METRICAS_VALIDAS)}",
        )
    return metrica


@router.get(
    "/afluencia",
    response_model=PrediccionAfluencia,
    summary="Predicción de afluencia (modelo estacional)",
)
async def afluencia(
    metrica: str = Query("totem", description="totem | web | app | chatbot"),
    horizonte_dias: int = Query(14, ge=1, le=120),
    dias_historico: int = Query(365, ge=30, le=1460),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PrediccionAfluencia:
    return await svc.prediccion_afluencia(
        db, _validar_metrica(metrica), horizonte_dias, dias_historico
    )


@router.get(
    "/validacion",
    response_model=ValidacionModelo,
    summary="Validación del modelo predictivo (MAPE / holdout temporal)",
)
async def validacion(
    metrica: str = Query("totem", description="totem | web | app | chatbot"),
    dias_historico: int = Query(365, ge=30, le=1460),
    dias_test: int = Query(14, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ValidacionModelo:
    return await svc.validacion_modelo(
        db, _validar_metrica(metrica), dias_historico, dias_test
    )


@router.get(
    "/anomalias",
    response_model=DeteccionAnomalias,
    summary="Detección de anomalías de afluencia (residuo estandarizado)",
)
async def anomalias(
    metrica: str = Query("totem", description="totem | web | app | chatbot"),
    dias_historico: int = Query(180, ge=30, le=1460),
    z: float = Query(3.0, ge=2.0, le=5.0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> DeteccionAnomalias:
    return await svc.anomalias_afluencia(db, _validar_metrica(metrica), dias_historico, z)
