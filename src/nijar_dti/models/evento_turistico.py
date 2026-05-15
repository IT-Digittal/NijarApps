"""Entidad EventoTuristico — Eventos del destino.

Compatible con FIWARE Smart Data Model `Event`.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class TipoEvento(StrEnum):
    """Tipos de evento turístico."""

    CULTURAL = "cultural"
    GASTRONOMICO = "gastronomico"
    DEPORTIVO = "deportivo"
    MUSICAL = "musical"
    FESTIVO = "festivo"
    NATURALEZA = "naturaleza"
    EDUCATIVO = "educativo"
    OTRO = "otro"


class EventoTuristico(Base, AuditMixin):
    """Evento turístico programado en el destino."""

    __tablename__ = "eventos_turisticos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    urn: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    tipo: Mapped[TipoEvento] = mapped_column(String(50), index=True)

    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ---- Campos opcionales (con default) ----
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)
    nombre_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)
    descripcion_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Recurso turístico asociado (puede ser opcional si es itinerante)
    recurso_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recursos_turisticos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Ubicación específica (puede diferir del recurso asociado)
    ubicacion: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        default=None,
    )
    direccion: Mapped[str | None] = mapped_column(String(500), default=None)

    organizador: Mapped[str | None] = mapped_column(String(255), default=None)
    precio: Mapped[str | None] = mapped_column(String(100), default=None)
    capacidad_aforo: Mapped[int | None] = mapped_column(default=None)

    enlace_inscripcion: Mapped[str | None] = mapped_column(String(500), default=None)
    imagenes: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    # Origen del dato (CMS manual / Facebook municipal / Instagram / web)
    fuente: Mapped[str | None] = mapped_column(String(100), default=None)

    activo: Mapped[bool] = mapped_column(default=True)
    publicado: Mapped[bool] = mapped_column(default=False)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_eventos_fechas", "fecha_inicio", "fecha_fin"),
        Index("ix_eventos_tipo_activo", "tipo", "activo"),
    )
