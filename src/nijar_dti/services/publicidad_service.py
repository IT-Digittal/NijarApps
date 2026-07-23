"""Lógica de negocio del módulo de publicidad (empresas anunciantes)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.empresa_anunciante import SECTORES_EMPRESA, EmpresaAnunciante
from nijar_dti.schemas.publicidad import EmpresaIn


class PublicidadError(Exception):
    pass


class EmpresaNoEncontradaError(PublicidadError):
    pass


def _validar(payload: EmpresaIn) -> None:
    if payload.sector not in SECTORES_EMPRESA:
        raise PublicidadError(
            f"Sector '{payload.sector}' no válido. Válidos: {', '.join(SECTORES_EMPRESA)}"
        )


async def crear_empresa(db: AsyncSession, payload: EmpresaIn) -> EmpresaAnunciante:
    _validar(payload)
    obj = EmpresaAnunciante(
        nombre=payload.nombre,
        sector=payload.sector,
        descripcion=payload.descripcion,
        descripcion_i18n=(
            payload.descripcion_i18n.model_dump(exclude_none=True)
            if payload.descripcion_i18n
            else None
        ),
        nucleo=payload.nucleo,
        direccion=payload.direccion,
        telefono=payload.telefono,
        web=payload.web,
        email=payload.email,
        imagenes=payload.imagenes,
        latitud=payload.latitud,
        longitud=payload.longitud,
        destacado=payload.destacado,
        prioridad=payload.prioridad,
        publicado=payload.publicado,
        campana_desde=payload.campana_desde,
        campana_hasta=payload.campana_hasta,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def listar_empresas(db: AsyncSession) -> tuple[list[EmpresaAnunciante], int]:
    filas = (
        (
            await db.execute(
                select(EmpresaAnunciante).order_by(
                    EmpresaAnunciante.destacado.desc(),
                    EmpresaAnunciante.prioridad.desc(),
                    EmpresaAnunciante.nombre,
                )
            )
        )
        .scalars()
        .all()
    )
    total = int(
        (await db.execute(select(func.count()).select_from(EmpresaAnunciante))).scalar_one() or 0
    )
    return list(filas), total


async def empresas_publicas(db: AsyncSession) -> list[EmpresaAnunciante]:
    """Empresas visibles AHORA en los canales públicos: publicadas y dentro de
    su ventana de campaña. Destacadas primero, luego por prioridad."""
    ahora = datetime.now(UTC)
    q = (
        select(EmpresaAnunciante)
        .where(
            EmpresaAnunciante.publicado.is_(True),
            or_(
                EmpresaAnunciante.campana_desde.is_(None),
                EmpresaAnunciante.campana_desde <= ahora,
            ),
            or_(
                EmpresaAnunciante.campana_hasta.is_(None),
                EmpresaAnunciante.campana_hasta >= ahora,
            ),
        )
        .order_by(
            EmpresaAnunciante.destacado.desc(),
            EmpresaAnunciante.prioridad.desc(),
            EmpresaAnunciante.nombre,
        )
    )
    return list((await db.execute(q)).scalars().all())


async def obtener_empresa(db: AsyncSession, empresa_id: UUID) -> EmpresaAnunciante:
    obj = await db.get(EmpresaAnunciante, empresa_id)
    if obj is None:
        raise EmpresaNoEncontradaError(f"Empresa {empresa_id} no encontrada")
    return obj


async def actualizar_empresa(
    db: AsyncSession, empresa_id: UUID, payload: EmpresaIn
) -> EmpresaAnunciante:
    _validar(payload)
    obj = await obtener_empresa(db, empresa_id)
    obj.nombre = payload.nombre
    obj.sector = payload.sector
    obj.descripcion = payload.descripcion
    obj.descripcion_i18n = (
        payload.descripcion_i18n.model_dump(exclude_none=True) if payload.descripcion_i18n else None
    )
    obj.nucleo = payload.nucleo
    obj.direccion = payload.direccion
    obj.telefono = payload.telefono
    obj.web = payload.web
    obj.email = payload.email
    obj.imagenes = payload.imagenes
    obj.latitud = payload.latitud
    obj.longitud = payload.longitud
    obj.destacado = payload.destacado
    obj.prioridad = payload.prioridad
    obj.publicado = payload.publicado
    obj.campana_desde = payload.campana_desde
    obj.campana_hasta = payload.campana_hasta
    await db.flush()
    await db.refresh(obj)
    return obj


async def eliminar_empresa(db: AsyncSession, empresa_id: UUID) -> None:
    obj = await obtener_empresa(db, empresa_id)
    await db.delete(obj)
    await db.flush()
