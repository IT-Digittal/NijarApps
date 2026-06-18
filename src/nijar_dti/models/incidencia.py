"""Entidad Incidencia — Ticketing del servicio de mantenimiento (C.1).

Registra las incidencias y acciones preventivas del mantenimiento, con sus
tiempos de detección, respuesta y resolución. Es la fuente real del informe
mensual de servicio: disponibilidad por componente, recuento por severidad,
tiempos y cumplimiento de la matriz ANS.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class SeveridadIncidencia(StrEnum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class EstadoIncidencia(StrEnum):
    ABIERTA = "abierta"
    EN_PROGRESO = "en_progreso"
    RESUELTA = "resuelta"
    CERRADA = "cerrada"


class OrigenIncidencia(StrEnum):
    MONITORIZACION = "monitorizacion"
    USUARIO = "usuario"
    TICKETING = "ticketing"
    PREVENTIVO = "preventivo"


class Incidencia(Base, TimestampMixin):
    """Incidencia o acción preventiva del mantenimiento (C.1)."""

    __tablename__ = "incidencias"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- obligatorios ----
    severidad: Mapped[SeveridadIncidencia] = mapped_column(String(20), index=True)
    titulo: Mapped[str] = mapped_column(String(255))
    componente: Mapped[str] = mapped_column(String(60), index=True)
    detectada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ---- opcionales con default ----
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)
    estado: Mapped[EstadoIncidencia] = mapped_column(
        String(20), default=EstadoIncidencia.ABIERTA, index=True
    )
    origen: Mapped[OrigenIncidencia] = mapped_column(
        String(20), default=OrigenIncidencia.TICKETING
    )
    # Si True, su duración cuenta como indisponibilidad del componente.
    afecta_disponibilidad: Mapped[bool] = mapped_column(Boolean, default=False)
    # Si True, es una acción preventiva ejecutada (no una incidencia reactiva).
    es_preventiva: Mapped[bool] = mapped_column(Boolean, default=False)
    es_evento_seguridad: Mapped[bool] = mapped_column(Boolean, default=False)
    incidente_confirmado: Mapped[bool] = mapped_column(Boolean, default=False)

    respondida_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    resuelta_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    __table_args__ = (
        Index("ix_incidencias_severidad_detectada", "severidad", "detectada_en"),
        Index("ix_incidencias_estado_detectada", "estado", "detectada_en"),
    )
