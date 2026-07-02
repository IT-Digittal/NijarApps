"""Lógica de negocio de la ficha del cliente / Ayuntamiento (bloque 1).

La plataforma gestiona un único cliente (el Ayuntamiento), por lo que la
ficha se comporta como un singleton: ``obtener_cliente`` devuelve la ficha
vigente y ``guardar_cliente`` la crea si no existe o la actualiza si ya está.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.cliente import Cliente
from nijar_dti.schemas.cliente import ClienteIn, ClienteUpdate


class NotFound(Exception):
    pass


async def obtener_cliente(db: AsyncSession) -> Cliente | None:
    """Devuelve la ficha del cliente vigente (o None si aún no existe)."""
    res = await db.execute(
        select(Cliente).where(Cliente.deleted_at.is_(None)).order_by(Cliente.created_at)
    )
    return res.scalars().first()


async def crear_cliente(db: AsyncSession, payload: ClienteIn) -> Cliente:
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    await db.flush()
    # Refrescar los valores calculados en servidor (created_at/updated_at)
    # para que la serialización de la respuesta no dispare IO síncrona.
    await db.refresh(cliente)
    return cliente


async def actualizar_cliente(db: AsyncSession, payload: ClienteUpdate) -> Cliente:
    cliente = await obtener_cliente(db)
    if cliente is None:
        raise NotFound("No existe una ficha de cliente")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    await db.flush()
    await db.refresh(cliente)
    return cliente


async def guardar_cliente(db: AsyncSession, payload: ClienteIn) -> Cliente:
    """Crea la ficha si no existe; si existe, la reemplaza con los datos dados."""
    cliente = await obtener_cliente(db)
    if cliente is None:
        return await crear_cliente(db, payload)
    for campo, valor in payload.model_dump().items():
        setattr(cliente, campo, valor)
    await db.flush()
    await db.refresh(cliente)
    return cliente
