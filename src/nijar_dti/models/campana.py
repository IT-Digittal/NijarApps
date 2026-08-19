"""Entidad Campana — Campañas de promoción turística (bloque 9 del pliego).

Registra las campañas de promoción del destino y permite medir su eficacia:
incremento de menciones/visitas, engagement, sentimiento durante la campaña y
comparativa con el periodo anterior.

Los KPIs de eficacia se calculan cruzando ``fecha_inicio``/``fecha_fin`` con las
menciones (``opiniones``) y las visitas (``visitas``) del periodo, usando la
etiqueta de campaña como enlace. Los objetivos y resultados agregados se
guardan en ``kpis_objetivo`` / ``resultados`` para trazabilidad del informe.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class EstadoCampana(StrEnum):
    """Ciclo de vida de una campaña de promoción."""

    PLANIFICADA = "planificada"
    ACTIVA = "activa"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class ObjetivoCampana(StrEnum):
    """Objetivo principal de la campaña (para segmentar KPIs)."""

    VISITAS = "visitas"
    MENCIONES = "menciones"
    DESCARGAS = "descargas"
    RESERVAS = "reservas"
    DIFUSION = "difusion"
    SENSIBILIZACION = "sensibilizacion"


class Campana(Base, AuditMixin):
    """Campaña de promoción turística del destino."""

    __tablename__ = "campanas"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- obligatorios ----
    nombre: Mapped[str] = mapped_column(String(255), index=True)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ---- opcionales con default ----
    # Etiqueta única para enlazar menciones/visitas (p. ej. "verano-2026").
    slug: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, default=None)

    descripcion: Mapped[str | None] = mapped_column(Text, default=None)
    objetivo: Mapped[ObjetivoCampana] = mapped_column(String(30), default=ObjetivoCampana.DIFUSION)
    publico_objetivo: Mapped[str | None] = mapped_column(String(255), default=None)

    # Canales usados: web, redes, email, app, prensa, ...
    canales: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    presupuesto: Mapped[float | None] = mapped_column(Numeric(12, 2), default=None)

    # Landing o recurso turístico asociado para medición digital
    landing_url: Mapped[str | None] = mapped_column(String(500), default=None)
    recurso_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recursos_turisticos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    estado: Mapped[EstadoCampana] = mapped_column(
        String(20), default=EstadoCampana.PLANIFICADA, index=True
    )

    # Objetivos numéricos: {"menciones": 500, "visitas_web": 2000, ...}
    kpis_objetivo: Mapped[dict | None] = mapped_column(JSON, default=None)
    # Resultados agregados calculados: {"menciones": ..., "visitas_web": ...,
    # "interacciones": ..., "alcance": ..., "sentimiento_positivo_pct": ...,
    # "incremento_menciones_pct": ..., "incremento_visitas_pct": ...}
    resultados: Mapped[dict | None] = mapped_column(JSON, default=None)

    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_campanas_fechas", "fecha_inicio", "fecha_fin"),
        Index("ix_campanas_estado_inicio", "estado", "fecha_inicio"),
    )
