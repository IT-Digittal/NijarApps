"""Datos eléctricos de Datadis (distribuidoras eléctricas).

- ``EnergiaMunicipioDiario``: consumo y nº de contratos de todo el municipio
  por día, sector económico y tensión (datos públicos agregados de Datadis).
- ``ConsumoHorarioEnergia``: curva de consumo horaria de cada suministro
  municipal (CUPS) obtenida con la API privada de Datadis. Los suministros en
  sí viven en ``SuministroEnergia`` (vertical de Energía).
"""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class EnergiaMunicipioDiario(Base, TimestampMixin):
    """Agregado diario público de Datadis para el municipio."""

    __tablename__ = "energia_municipio_diario"
    __table_args__ = (
        UniqueConstraint("fecha", "sector", "tension", name="uq_energia_municipio_dia"),
        Index("ix_energia_municipio_fecha", "fecha"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    fecha: Mapped[date] = mapped_column(Date)
    sector: Mapped[str] = mapped_column(String(60))
    tension: Mapped[str] = mapped_column(String(60))
    contratos: Mapped[int] = mapped_column(Integer, default=0)
    energia_kwh: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    municipio: Mapped[str] = mapped_column(String(80), default="NÍJAR")
    fuente: Mapped[str] = mapped_column(String(30), default="datadis")


class ConsumoHorarioEnergia(Base, TimestampMixin):
    """Lectura horaria de un suministro municipal (API privada de Datadis)."""

    __tablename__ = "energia_consumos_horarios"
    __table_args__ = (
        UniqueConstraint("cups", "momento", name="uq_energia_consumo_cups_momento"),
        Index("ix_energia_consumos_cups_momento", "cups", "momento"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    cups: Mapped[str] = mapped_column(String(30))
    momento: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # inicio de la hora
    consumo_kwh: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    excedente_kwh: Mapped[float | None] = mapped_column(Numeric(12, 4), default=None)
    autoconsumo_kwh: Mapped[float | None] = mapped_column(Numeric(12, 4), default=None)
    metodo: Mapped[str | None] = mapped_column(String(20), default=None)  # Real / Estimada
