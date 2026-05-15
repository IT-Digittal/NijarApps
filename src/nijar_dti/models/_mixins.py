"""Mixin de auditoría para los modelos ORM.

Cumple con el requisito ENS Medio de trazabilidad: cada entidad registra
quién y cuándo la creó, modificó o eliminó (soft delete).

Todos los campos del mixin se declaran con ``kw_only=True`` para que el
orden de los argumentos positionales en el dataclass generado por
SQLAlchemy 2.0 (``MappedAsDataclass``) no entre en conflicto con los
campos obligatorios de los modelos que heredan del mixin.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Añade timestamps automáticos de creación y modificación."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        init=False,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
        nullable=False,
    )


class AuditMixin(TimestampMixin):
    """Auditoría completa: timestamps + autoría + soft delete."""

    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        default=None,
        kw_only=True,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        default=None,
        kw_only=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        kw_only=True,
    )
