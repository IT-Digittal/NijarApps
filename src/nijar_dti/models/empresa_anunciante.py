"""Empresas anunciantes — módulo de publicidad del destino.

Negocios locales (restaurantes, alojamientos, ocio activo, comercio…) que
contratan presencia en los canales públicos del destino: hoy el apartado
«Empresas» del tótem; mañana web y app. La campaña puede acotarse con una
ventana de fechas y ordenarse con destacados y prioridad.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin

SECTORES_EMPRESA = (
    "gastronomia",
    "alojamiento",
    "ocio_activo",
    "comercio",
    "servicios",
    "otro",
)


class EmpresaAnunciante(Base, TimestampMixin):
    """Una empresa local con presencia publicitaria en los canales del destino."""

    __tablename__ = "empresas_anunciantes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    sector: Mapped[str] = mapped_column(String(30), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)
    descripcion_i18n: Mapped[dict[str, str] | None] = mapped_column(JSON, default=None)

    nucleo: Mapped[str | None] = mapped_column(String(120), default=None)  # San José, Níjar…
    direccion: Mapped[str | None] = mapped_column(String(255), default=None)
    telefono: Mapped[str | None] = mapped_column(String(40), default=None)
    web: Mapped[str | None] = mapped_column(String(255), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    imagenes: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    latitud: Mapped[float | None] = mapped_column(Float, default=None)
    longitud: Mapped[float | None] = mapped_column(Float, default=None)

    # Campaña publicitaria
    destacado: Mapped[bool] = mapped_column(Boolean, default=False)
    prioridad: Mapped[int] = mapped_column(Integer, default=0)  # mayor = antes
    publicado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    campana_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    campana_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class MetricaPublicidad(Base, TimestampMixin):
    """Agregado diario de visibilidad de un anunciante en el tótem.

    - ``impresiones``: veces que la tarjeta se mostró en pantalla.
    - ``toques``: veces que un visitante tocó la tarjeta.
    El tótem las envía en lotes anónimos; sirven para justificar la
    facturación de las campañas.
    """

    __tablename__ = "metricas_publicidad"
    __table_args__ = (UniqueConstraint("empresa_id", "fecha", name="uq_metricas_publicidad_dia"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )
    empresa_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("empresas_anunciantes.id", ondelete="CASCADE"),
        index=True,
    )
    fecha: Mapped[date] = mapped_column(Date, index=True)
    impresiones: Mapped[int] = mapped_column(Integer, default=0)
    toques: Mapped[int] = mapped_column(Integer, default=0)
