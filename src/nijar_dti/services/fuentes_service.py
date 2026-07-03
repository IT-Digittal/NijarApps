"""Lógica del catálogo de fuentes de datos e integraciones."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.fuente_dato import FuenteDato
from nijar_dti.schemas.fuentes import FuenteDatoOut, FuentesResumen


async def listar_fuentes(
    db: AsyncSession,
    origen: str | None = None,
    estado: str | None = None,
    categoria: str | None = None,
) -> list[FuenteDatoOut]:
    q = select(FuenteDato)
    if origen:
        q = q.where(FuenteDato.origen == origen)
    if estado:
        q = q.where(FuenteDato.estado == estado)
    if categoria:
        q = q.where(FuenteDato.categoria == categoria)
    q = q.order_by(FuenteDato.codigo)
    filas = (await db.execute(q)).scalars().all()
    return [FuenteDatoOut.model_validate(f) for f in filas]


async def resumen_fuentes(db: AsyncSession) -> FuentesResumen:
    filas = list((await db.execute(select(FuenteDato))).scalars().all())
    return FuentesResumen(
        total=len(filas),
        propias=sum(1 for f in filas if f.origen == "propia"),
        externas=sum(1 for f in filas if f.origen == "externa"),
        operativas=sum(1 for f in filas if f.estado == "operativa"),
        pendiente_desarrollo=sum(1 for f in filas if f.estado == "pendiente_desarrollo"),
        pendiente_acceso=sum(1 for f in filas if f.estado == "pendiente_acceso"),
        requieren_credenciales=sum(1 for f in filas if f.requiere_credenciales),
        por_categoria=dict(Counter(f.categoria for f in filas)),
        por_estado=dict(Counter(f.estado for f in filas)),
    )
