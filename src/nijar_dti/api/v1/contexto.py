"""Endpoints de contexto histórico (backfill de fuentes públicas oficiales)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.contexto import (
    ContextoIngestIn,
    ContextoIngestResult,
    ContextoSerie,
    FactorExpansionOut,
)
from nijar_dti.services import contexto_service as svc

router = APIRouter()


@router.post(
    "/ingest",
    response_model=ContextoIngestResult,
    summary="Ingesta idempotente de series de contexto (backfill INE/Junta/AENA)",
)
async def ingest(
    body: ContextoIngestIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("administrador_tic", "analista_datos")),
) -> ContextoIngestResult:
    return await svc.ingerir_registros(db, body.registros)


@router.get(
    "/series",
    response_model=ContextoSerie,
    summary="Serie histórica de un indicador de contexto",
)
async def series(
    fuente: str = Query(..., description="ine_frontur|ine_egatur|ine_eoh|junta_andalucia|aena"),
    indicador: str = Query(...),
    ambito: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ContextoSerie:
    return await svc.obtener_serie(db, fuente, indicador, ambito)


@router.get(
    "/factor-expansion",
    response_model=FactorExpansionOut,
    summary="Factor de expansión calibrado contra pernoctaciones EOH",
)
async def factor_expansion(
    periodo: str | None = Query(None, description="AAAA-MM; por defecto el último EOH disponible"),
    muestra_periodo: int | None = Query(
        None, description="Tamaño de la muestra propia (p. ej. conexiones WiFi únicas)"
    ),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> FactorExpansionOut:
    fe, periodo_ref = await svc.factor_expansion(db, periodo, muestra_periodo)
    return FactorExpansionOut(
        factor=fe.factor,
        cobertura_estimada_pct=fe.cobertura_estimada_pct,
        metodo=fe.metodo,
        muestra_referencia=fe.muestra_referencia,
        visitantes_oficiales_estimados=fe.visitantes_oficiales_estimados,
        es_preliminar=fe.es_preliminar,
        periodo_referencia=periodo_ref,
        calculado_en=datetime.now(timezone.utc),
    )
