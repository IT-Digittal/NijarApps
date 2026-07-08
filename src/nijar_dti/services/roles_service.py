"""Lógica de negocio para gestión de roles y sus permisos (BD)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core import permisos as catalogo
from nijar_dti.models.rol import Rol
from nijar_dti.models.usuario import RolUsuario, Usuario

_MODULOS_IDS: set[str] = {m["id"] for m in catalogo.MODULOS}
_SUPERADMIN = RolUsuario.ADMINISTRADOR_TIC.value


class RolNoEncontradoError(Exception):
    """No existe un rol con ese slug."""


class RolYaExisteError(Exception):
    """Ya existe un rol con ese slug."""


class OperacionRolNoPermitidaError(Exception):
    """La operación sobre el rol no está permitida (rol de sistema, en uso, etc.)."""


def _validar_permisos(permisos: list[str]) -> list[str]:
    """Normaliza y valida que todos los permisos existen en el catálogo."""
    limpios = sorted(set(permisos))
    desconocidos = [p for p in limpios if p not in _MODULOS_IDS]
    if desconocidos:
        raise OperacionRolNoPermitidaError(f"Permisos desconocidos: {desconocidos}")
    return limpios


async def contar_usuarios_por_rol(db: AsyncSession) -> dict[str, int]:
    """Nº de usuarios activos (no borrados) por slug de rol."""
    stmt = (
        select(Usuario.rol, func.count())
        .where(Usuario.deleted_at.is_(None))
        .group_by(Usuario.rol)
    )
    res = await db.execute(stmt)
    return {rol: int(n) for rol, n in res.all()}


async def listar_roles(db: AsyncSession) -> list[Rol]:
    res = await db.execute(
        select(Rol).where(Rol.deleted_at.is_(None)).order_by(Rol.es_sistema.desc(), Rol.display)
    )
    return list(res.scalars().all())


async def obtener_rol(db: AsyncSession, slug: str) -> Rol:
    res = await db.execute(
        select(Rol).where(Rol.slug == slug).where(Rol.deleted_at.is_(None))
    )
    rol = res.scalar_one_or_none()
    if rol is None:
        raise RolNoEncontradoError(f"No existe el rol '{slug}'")
    return rol


async def permisos_de_rol(db: AsyncSession, slug: str) -> set[str]:
    """Permisos de un rol desde BD; si no existe, cae al catálogo semilla."""
    res = await db.execute(
        select(Rol.permisos).where(Rol.slug == slug).where(Rol.deleted_at.is_(None))
    )
    fila = res.scalar_one_or_none()
    if fila is not None:
        return set(fila or [])
    return set(catalogo.PERMISOS_POR_ROL.get(slug, set()))


async def crear_rol(
    db: AsyncSession,
    *,
    slug: str,
    display: str,
    permisos: list[str],
    descripcion: str | None = None,
    actor: Usuario | None = None,
) -> Rol:
    existe = await db.execute(select(Rol.id).where(Rol.slug == slug))
    if existe.scalar_one_or_none() is not None:
        raise RolYaExisteError(f"Ya existe un rol con slug '{slug}'")
    rol = Rol(
        slug=slug,
        display=display,
        descripcion=descripcion,
        permisos=_validar_permisos(permisos),
        es_sistema=False,
        created_by=actor.id if actor else None,
    )
    db.add(rol)
    await db.commit()
    await db.refresh(rol)
    return rol


async def actualizar_rol(
    db: AsyncSession,
    slug: str,
    *,
    display: str | None = None,
    descripcion: str | None = None,
    permisos: list[str] | None = None,
    actor: Usuario | None = None,
) -> Rol:
    rol = await obtener_rol(db, slug)
    if display is not None:
        rol.display = display
    if descripcion is not None:
        rol.descripcion = descripcion
    if permisos is not None:
        nuevos = _validar_permisos(permisos)
        # El superadministrador siempre conserva TODOS los permisos.
        if rol.slug == _SUPERADMIN:
            nuevos = sorted(_MODULOS_IDS)
        rol.permisos = nuevos
    if actor is not None:
        rol.updated_by = actor.id
    await db.commit()
    await db.refresh(rol)
    return rol


async def eliminar_rol(db: AsyncSession, slug: str, actor: Usuario | None = None) -> None:
    rol = await obtener_rol(db, slug)
    if rol.es_sistema:
        raise OperacionRolNoPermitidaError("No se puede eliminar un rol de sistema.")
    conteo = await contar_usuarios_por_rol(db)
    if conteo.get(slug, 0) > 0:
        raise OperacionRolNoPermitidaError(
            "El rol tiene usuarios asignados. Reasígnalos antes de eliminarlo."
        )
    rol.deleted_at = datetime.now(UTC)
    if actor is not None:
        rol.updated_by = actor.id
    await db.commit()


async def existe_rol(db: AsyncSession, slug: str) -> bool:
    res = await db.execute(
        select(Rol.id).where(Rol.slug == slug).where(Rol.deleted_at.is_(None))
    )
    return res.scalar_one_or_none() is not None


async def matriz(db: AsyncSession) -> dict[str, object]:
    """Matriz roles × módulos (DB-backed) para el panel de administración."""
    roles = await listar_roles(db)
    conteo = await contar_usuarios_por_rol(db)
    return {
        "modulos": catalogo.MODULOS,
        "roles": [
            {
                "rol": r.slug,
                "display": r.display,
                "permisos": sorted(r.permisos or []),
                "es_sistema": r.es_sistema,
                "n_usuarios": conteo.get(r.slug, 0),
            }
            for r in roles
        ],
    }
