"""Entidad Rol — roles RBAC con sus permisos, editables desde el panel.

A diferencia del enum `RolUsuario` (que fija los roles integrados en código),
esta tabla permite al administrador **crear roles nuevos y editar los permisos**
de cada rol. Los roles integrados se siembran con `es_sistema=True`: sus
permisos se pueden ajustar pero no se pueden borrar. El catálogo de permisos
posibles (`MODULOS`) sigue viviendo en `nijar_dti.core.permisos`.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class Rol(Base, AuditMixin):
    """Rol RBAC con su conjunto de permisos (ids de módulo)."""

    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(255), default=None)
    permisos: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    es_sistema: Mapped[bool] = mapped_column(default=False)
