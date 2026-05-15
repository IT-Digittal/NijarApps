"""Entidad Observacion — Lecturas/medidas de los sensores.

Compatible con FIWARE Smart Data Model `AirQualityObserved` y `WeatherObserved`.
Esta tabla está optimizada para volúmenes elevados (TimescaleDB compatible).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class Observacion(Base, TimestampMixin):
    """Observación / medida puntual de un sensor.

    Diseñada para alta cardinalidad: una fila por cada lectura. Particionable
    por tiempo en producción usando TimescaleDB o partitioning nativo de PG.
    """

    __tablename__ = "observaciones"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    sensor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensores.id", ondelete="CASCADE"),
        index=True,
    )

    # Timestamp del evento (puede diferir del created_at)
    observado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )

    # Valor numérico (la mayoría de sensores)
    valor: Mapped[float | None] = mapped_column(Numeric(12, 4), default=None)
    unidades: Mapped[str | None] = mapped_column(String(50), default=None)

    # Para lecturas multi-valor (ej. estación meteo: temp+viento+humedad)
    valores: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Calidad del dato
    valido: Mapped[bool] = mapped_column(default=True)
    motivo_invalidez: Mapped[str | None] = mapped_column(String(255), default=None)

    # Metadatos del payload original (linaje del dato — ENS Medio)
    payload_original: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_observaciones_sensor_tiempo", "sensor_id", "observado_en"),
        Index("ix_observaciones_tiempo", "observado_en"),
    )
