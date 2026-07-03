"""Vertical Alumbrado público — gemelo digital de la red de alumbrado.

Modela la jerarquía municipio → zona → cuadro de mando → luminaria del
Centro de Control de Alumbrado, con la telegestión punto a punto: tecnología,
potencia, estado operativo, comunicaciones y consumo. Es la fuente de los
KPIs de disponibilidad, eficiencia energética y ahorro de la vertical.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class TecnologiaLuminaria(StrEnum):
    LED = "led"
    VSAP = "vsap"  # Vapor de sodio de alta presión
    SOLAR = "solar"


class EstadoActivo(StrEnum):
    OPERATIVO = "operativo"
    ALERTA = "alerta"
    AVERIA = "averia"
    SIN_COMUNICACION = "sin_comunicacion"


class ZonaAlumbrado(Base, TimestampMixin):
    """Zona/núcleo del municipio con su parque de luminarias agregado."""

    __tablename__ = "alumbrado_zonas"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # slug: nijar, sanjose...
    nombre: Mapped[str] = mapped_column(String(120))
    luminarias: Mapped[int] = mapped_column(default=0)
    led: Mapped[int] = mapped_column(default=0)
    vsap: Mapped[int] = mapped_column(default=0)
    solar: Mapped[int] = mapped_column(default=0)
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)


class CuadroMando(Base, TimestampMixin):
    """Cuadro de mando de alumbrado (CM): agrupa circuitos y luminarias."""

    __tablename__ = "alumbrado_cuadros"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CM-001
    nombre: Mapped[str] = mapped_column(String(120))
    zona_id: Mapped[str] = mapped_column(String(40), index=True)
    ubicacion: Mapped[str | None] = mapped_column(String(255), default=None)
    circuitos: Mapped[int] = mapped_column(default=0)
    potencia_kw: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    factor_potencia: Mapped[float | None] = mapped_column(Numeric(4, 2), default=None)
    comunicaciones: Mapped[str] = mapped_column(String(30), default="online")
    sla: Mapped[int] = mapped_column(default=99)
    estado: Mapped[EstadoActivo] = mapped_column(
        String(30), default=EstadoActivo.OPERATIVO, index=True
    )
    alarmas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)


class Luminaria(Base, TimestampMixin):
    """Punto de luz individual (activo del gemelo digital)."""

    __tablename__ = "alumbrado_luminarias"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # L-0001
    zona_id: Mapped[str] = mapped_column(String(40), index=True)
    tecnologia: Mapped[TecnologiaLuminaria] = mapped_column(String(20), index=True)

    cuadro_codigo: Mapped[str | None] = mapped_column(String(20), index=True, default=None)
    circuito: Mapped[str | None] = mapped_column(String(30), default=None)
    direccion: Mapped[str | None] = mapped_column(String(255), default=None)

    potencia_w: Mapped[int] = mapped_column(default=0)
    marca_modelo: Mapped[str | None] = mapped_column(String(120), default=None)
    anio_instalacion: Mapped[int | None] = mapped_column(default=None)
    vida_util_h: Mapped[int | None] = mapped_column(default=None)

    estado: Mapped[EstadoActivo] = mapped_column(
        String(30), default=EstadoActivo.OPERATIVO, index=True
    )
    nivel_regulacion: Mapped[int] = mapped_column(default=100)  # % dimming
    horas_funcionamiento: Mapped[int | None] = mapped_column(default=None)
    consumo_mes_kwh: Mapped[float | None] = mapped_column(Numeric(8, 2), default=None)
    ultima_comunicacion_min: Mapped[int | None] = mapped_column(default=None)
    tiene_documentacion: Mapped[bool] = mapped_column(default=True)

    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_luminarias_zona_estado", "zona_id", "estado"),
        Index("ix_luminarias_tecnologia", "tecnologia"),
    )
