"""Normativa municipal: ordenanzas y documentos de la sede electrónica.

Cada ``Normativa`` es un PDF descargado del portal de transparencia (ordenanza,
reglamento, edicto, proyecto, certificado…) con su texto extraído. El texto se
parte en ``NormativaFragmento`` (un artículo o un trozo de ~1.500 caracteres)
para que el buscador y el asistente encuentren y citen el pasaje concreto.

La búsqueda usa el texto completo de PostgreSQL en español (índices GIN sobre
``to_tsvector('spanish', …)``, migración 020).
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class Normativa(Base, TimestampMixin):
    """Un documento normativo municipal (PDF) con su texto."""

    __tablename__ = "normativas"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    titulo: Mapped[str] = mapped_column(String(500))
    tipo: Mapped[str] = mapped_column(String(30), index=True)  # ordenanza, reglamento…
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    fichero: Mapped[str] = mapped_column(String(255))  # ruta relativa en STORAGE_LOCAL_PATH
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    paginas: Mapped[int] = mapped_column(Integer, default=0)
    texto: Mapped[str] = mapped_column(Text, default="")
    url_origen: Mapped[str | None] = mapped_column(String(500), default=None)
    fecha_publicacion: Mapped[date | None] = mapped_column(Date, default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadatos: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class NormativaFragmento(Base):
    """Un artículo o pasaje de una normativa (unidad de búsqueda y de cita)."""

    __tablename__ = "normativa_fragmentos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    normativa_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("normativas.id", ondelete="CASCADE"), index=True
    )
    orden: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)
    articulo: Mapped[str | None] = mapped_column(String(160), default=None)
