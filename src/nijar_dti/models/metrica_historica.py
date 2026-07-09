"""Serie histórica mensual de métricas por vertical Smart City.

A diferencia de los overviews (foto del mes actual), esta tabla guarda un punto
por (vertical, indicador, periodo) de modo que se pueda calcular la comparativa
interanual REAL de energía, agua, residuos, movilidad, seguridad y alumbrado
(consumo, coste/facturación, toneladas, incidencias…). El seeder genera 2 años
de histórico; en producción se poblaría capturando una foto cada mes.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Float, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class MetricaHistorica(Base, TimestampMixin):
    """Un valor mensual de un indicador de una vertical (serie histórica)."""

    __tablename__ = "metricas_historicas"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    vertical: Mapped[str] = mapped_column(String(30), index=True)
    indicador: Mapped[str] = mapped_column(String(60), index=True)
    periodo: Mapped[str] = mapped_column(String(10), index=True)  # "2025-06"
    valor: Mapped[float] = mapped_column(Float)
    unidad: Mapped[str | None] = mapped_column(String(20), default=None)

    __table_args__ = (
        Index(
            "ux_metricas_hist_vertical_indicador_periodo",
            "vertical",
            "indicador",
            "periodo",
            unique=True,
        ),
    )
