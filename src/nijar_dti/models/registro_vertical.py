"""Registro de eventos de las verticales Smart City.

Cada fila es algo que ha pasado en un momento dado en una vertical: una cámara
que pierde la comunicación, un contenedor que supera el 90 % de llenado, una
lectura de un sensor IoT, una carga de Datadis, la importación del inventario
de alumbrado… Es el «log» que se consulta con filtros en la sección
«Registros» de cada vertical.

``EstadoActivo`` guarda el último estado conocido de cada activo para que el
detector de cambios (``registros_service.detectar_cambios``) solo registre las
transiciones, no la foto completa cada vez.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class RegistroVertical(Base, TimestampMixin):
    """Un evento de una vertical (alarma, cambio de estado, lectura, carga…)."""

    __tablename__ = "registros_verticales"
    __table_args__ = (
        Index("ix_registros_vertical_momento", "vertical", "momento"),
        Index("ix_registros_activo", "vertical", "activo_codigo"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    vertical: Mapped[str] = mapped_column(String(20))  # alumbrado, agua, residuos…
    tipo: Mapped[str] = mapped_column(String(20), index=True)  # alarma, estado, lectura…
    severidad: Mapped[str] = mapped_column(String(10), index=True)  # info | aviso | critico
    mensaje: Mapped[str] = mapped_column(Text)
    momento: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    activo_codigo: Mapped[str | None] = mapped_column(String(60), default=None)
    activo_nombre: Mapped[str | None] = mapped_column(String(200), default=None)
    origen: Mapped[str] = mapped_column(String(30), default="plataforma")  # mqtt, datadis…
    datos: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class EstadoActivo(Base, TimestampMixin):
    """Último estado conocido de un activo (para registrar solo los cambios)."""

    __tablename__ = "estados_activos"
    __table_args__ = (UniqueConstraint("vertical", "codigo", name="uq_estado_activo"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    vertical: Mapped[str] = mapped_column(String(20))
    codigo: Mapped[str] = mapped_column(String(60))
    estado: Mapped[str] = mapped_column(String(60))
