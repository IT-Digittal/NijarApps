"""Entidad Contenido — Contenidos publicables del CMS centralizado."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class EstadoContenido(StrEnum):
    """Ciclo de vida del contenido.

    El flujo editorial completo (borrador → pendiente_aprobacion → aprobado →
    publicado → archivado) permite medir el KPI del pliego "tiempo de
    publicación de contenidos" (≤ 24 h desde la aprobación) a partir de
    ``fecha_aprobacion`` y ``fecha_publicacion``.
    """

    BORRADOR = "borrador"
    PENDIENTE_APROBACION = "pendiente_aprobacion"
    APROBADO = "aprobado"
    PROGRAMADO = "programado"
    PUBLICADO = "publicado"
    ARCHIVADO = "archivado"


class Contenido(Base, AuditMixin):
    """Pieza de contenido publicable a través de los canales del destino."""

    __tablename__ = "contenidos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- campos obligatorios (sin default) ----
    titulo: Mapped[str] = mapped_column(String(255), index=True)
    cuerpo: Mapped[str] = mapped_column(Text)

    # ---- campos con default ----
    titulo_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)
    cuerpo_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)

    canales: Mapped[list[str]] = mapped_column(ARRAY(String), default_factory=list)
    plantilla_id: Mapped[str | None] = mapped_column(String(100), default=None)

    recurso_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recursos_turisticos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    estado: Mapped[EstadoContenido] = mapped_column(
        String(20), default=EstadoContenido.BORRADOR, index=True
    )
    publicar_desde: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    publicar_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Trazabilidad del flujo editorial (KPI de tiempo de publicación ≤ 24 h)
    fecha_aprobacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    fecha_publicacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    imagenes: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    enlaces: Mapped[dict | None] = mapped_column(JSON, default=None)
    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_contenidos_estado_publicar", "estado", "publicar_desde"),
    )
