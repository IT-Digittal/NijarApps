"""Estado persistido de las recomendaciones de dirección.

Las recomendaciones se generan al vuelo (reglas u OpenAI), pero su ciclo de
vida (pendiente → aceptada/descartada/ejecutada) y el comentario de dirección
se guardan aquí, identificados por una `clave` estable derivada del área y el
título, de modo que al regenerar la lista se conserva el estado.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class RecomendacionDireccion(Base, AuditMixin):
    """Estado y comentario de una recomendación ejecutiva."""

    __tablename__ = "recomendaciones_direccion"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    clave: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255))
    area: Mapped[str] = mapped_column(String(80))
    prioridad: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    comentario: Mapped[str | None] = mapped_column(String(500), default=None)
