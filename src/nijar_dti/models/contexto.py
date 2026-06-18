"""Entidad ContextoTuristico — Series históricas de fuentes públicas oficiales.

Almacena el "background poblacional" del observatorio: indicadores
turísticos oficiales de organismos públicos (INE, Junta de Andalucía, AENA)
que aportan histórico largo contra el que comparar la realidad municipal y
calibrar el factor de expansión de las señales muestrales (WiFi/beacons).

Se cargan mediante el conector de backfill (``connectors/contexto``) y son
de acceso libre / datos abiertos, por lo que no contienen datos personales.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class FuenteContexto(StrEnum):
    """Organismos públicos origen de las series de contexto."""

    INE_FRONTUR = "ine_frontur"  # Turismo internacional (mensual)
    INE_EGATUR = "ine_egatur"  # Gasto turístico (trimestral)
    INE_EOH = "ine_eoh"  # Encuesta de Ocupación Hotelera (mensual)
    JUNTA_ANDALUCIA = "junta_andalucia"  # Observatorio Turístico de Andalucía
    AENA = "aena"  # Pasajeros Aeropuerto de Almería (mensual)


class ContextoTuristico(Base, TimestampMixin):
    """Observación de una serie histórica oficial (un indicador en un periodo)."""

    __tablename__ = "contexto_turistico"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- campos obligatorios ----
    fuente: Mapped[FuenteContexto] = mapped_column(String(40), index=True)
    indicador: Mapped[str] = mapped_column(String(120), index=True)
    periodo: Mapped[str] = mapped_column(String(10), index=True)  # "2024-07" | "2024-Q3" | "2024"
    valor: Mapped[float] = mapped_column(Numeric(18, 4))

    # ---- campos opcionales con default ----
    unidad: Mapped[str | None] = mapped_column(String(40), default=None)
    ambito: Mapped[str] = mapped_column(String(40), default="provincia_almeria", index=True)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)
    capturado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    __table_args__ = (
        # Idempotencia: un único registro por (fuente, indicador, periodo, ámbito)
        Index(
            "ux_contexto_fuente_indicador_periodo_ambito",
            "fuente",
            "indicador",
            "periodo",
            "ambito",
            unique=True,
        ),
    )
