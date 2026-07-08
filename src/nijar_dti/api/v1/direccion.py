"""Endpoints del Cuadro de Mando de Dirección (perfil ejecutivo/político)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import require_permiso
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.direccion import (
    EstadoRecomendacionUpdate,
    RecomendacionIA,
    ResumenMunicipal,
)
from nijar_dti.services import direccion_service, recomendaciones_service, usuarios_service

router = APIRouter()

_ver_direccion = require_permiso("ver_resumen_municipal")
_ver_recomendaciones = require_permiso("ver_recomendaciones_ia")


@router.get(
    "/resumen",
    response_model=ResumenMunicipal,
    summary="Resumen municipal ejecutivo (estado global, semáforo, alertas, impacto)",
)
async def resumen(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_ver_direccion),
) -> ResumenMunicipal:
    return await direccion_service.resumen_municipal(db)


@router.get(
    "/recomendaciones",
    response_model=list[RecomendacionIA],
    summary="Recomendaciones para dirección (motor de reglas)",
)
async def recomendaciones(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_ver_recomendaciones),
) -> list[RecomendacionIA]:
    return await recomendaciones_service.generar(db)


@router.patch(
    "/recomendaciones/{clave}",
    response_model=RecomendacionIA,
    summary="Cambiar el estado / comentario de una recomendación",
)
async def actualizar_recomendacion(
    clave: str,
    payload: EstadoRecomendacionUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(_ver_recomendaciones),
) -> RecomendacionIA:
    try:
        actor = await usuarios_service.obtener_usuario(db, current.id)
        return await recomendaciones_service.actualizar_estado(
            db, clave, estado=payload.estado, comentario=payload.comentario, actor=actor
        )
    except recomendaciones_service.RecomendacionNoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
