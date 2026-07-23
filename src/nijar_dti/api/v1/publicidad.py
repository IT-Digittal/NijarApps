"""Endpoints del módulo de publicidad (empresas anunciantes).

CRUD para el panel (roles de gestión) y un endpoint público que consume el
apartado «Empresas» del tótem: solo empresas publicadas y dentro de su
ventana de campaña, sin datos de gestión.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.api.v1.dependencies import get_current_user, require_roles
from nijar_dti.core.database import get_db
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.publicidad import (
    EmpresaIn,
    EmpresaOut,
    EmpresaPublicaOut,
    EmpresasPage,
    LoteMetricasIn,
    ResumenMetricasOut,
)
from nijar_dti.services import informe_publicidad as informe_svc
from nijar_dti.services import publicidad_service as svc

router = APIRouter()

_puede_gestionar = require_roles("administrador_tic", "gestor_contenidos")


@router.get(
    "/publico/totem",
    response_model=list[EmpresaPublicaOut],
    summary="Empresas anunciantes visibles en el tótem (público)",
)
async def empresas_publicas_totem(db: AsyncSession = Depends(get_db)) -> list[EmpresaPublicaOut]:
    filas = await svc.empresas_publicas(db)
    return [EmpresaPublicaOut.model_validate(e) for e in filas]


@router.post(
    "/publico/metricas",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Registrar impresiones/toques desde el tótem (público, anónimo)",
)
async def registrar_metricas_totem(
    lote: LoteMetricasIn, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Lote anónimo de eventos de visibilidad. Los IDs desconocidos se
    descartan en silencio; no hay datos personales implicados."""
    registrados = await svc.registrar_metricas(db, lote.eventos)
    await db.commit()
    return {"empresas_actualizadas": registrados}


@router.get(
    "/metricas",
    response_model=ResumenMetricasOut,
    summary="Resumen de impresiones/toques por anunciante (facturación)",
)
async def resumen_metricas(
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ResumenMetricasOut:
    dias = max(1, min(dias, 365))
    return ResumenMetricasOut(dias=dias, metricas=await svc.resumen_metricas(db, dias))


@router.get(
    "/{empresa_id}/informe",
    summary="Informe mensual de visibilidad del anunciante (PDF)",
)
async def informe_pdf(
    empresa_id: UUID,
    anio: int,
    mes: int,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Justificante de campaña para la facturación: impresiones y toques del
    mes, desglosados por semana, con metodología al pie."""
    if not 1 <= mes <= 12 or not 2020 <= anio <= 2100:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mes o año no válidos")
    try:
        datos = await informe_svc.datos_informe(db, empresa_id, anio, mes)
    except svc.EmpresaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    pdf = informe_svc.render_pdf(datos)
    nombre = f"informe-publicidad-{anio}-{mes:02d}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("", response_model=EmpresasPage, summary="Listar empresas anunciantes")
async def listar(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> EmpresasPage:
    filas, total = await svc.listar_empresas(db)
    return EmpresasPage(items=[EmpresaOut.model_validate(e) for e in filas], total=total)


@router.post(
    "",
    response_model=EmpresaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una empresa anunciante",
)
async def crear(
    payload: EmpresaIn,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> EmpresaOut:
    try:
        obj = await svc.crear_empresa(db, payload)
    except svc.PublicidadError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.commit()
    return EmpresaOut.model_validate(obj)


@router.put("/{empresa_id}", response_model=EmpresaOut, summary="Actualizar empresa anunciante")
async def actualizar(
    empresa_id: UUID,
    payload: EmpresaIn,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> EmpresaOut:
    try:
        obj = await svc.actualizar_empresa(db, empresa_id, payload)
    except svc.EmpresaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except svc.PublicidadError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.commit()
    return EmpresaOut.model_validate(obj)


@router.delete(
    "/{empresa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar empresa anunciante",
)
async def eliminar(
    empresa_id: UUID,
    user: Annotated[CurrentUser, Depends(_puede_gestionar)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await svc.eliminar_empresa(db, empresa_id)
    except svc.EmpresaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await db.commit()
