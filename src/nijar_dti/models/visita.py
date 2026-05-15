"""Entidad Visita — Interacciones de visitantes con el destino.

Cubre los eventos de proximidad BLE, las interacciones con tótems,
las consultas al chatbot y otros eventos de contacto digital con el
visitante. Datos siempre anonimizados (RGPD).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class TipoVisita(StrEnum):
    """Tipos de evento de visita."""

    PROXIMIDAD_BLE = "proximidad_ble"
    INTERACCION_TOTEM = "interaccion_totem"
    CONSULTA_CHATBOT = "consulta_chatbot"
    APP_VISTA = "app_vista"
    WEB_VISTA = "web_vista"
    WIFI_CONEXION = "wifi_conexion"


class Visita(Base, TimestampMixin):
    """Evento de visita / interacción con el destino (anonimizado)."""

    __tablename__ = "visitas"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    tipo: Mapped[TipoVisita] = mapped_column(String(40), index=True)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # Identificador anonimizado (hash SHA-256 de MAC u otro identificador)
    visitante_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    # Recurso turístico asociado (POI visitado, totem consultado...)
    recurso_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recursos_turisticos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Idioma detectado (relevante para chatbot/tótem)
    idioma: Mapped[str | None] = mapped_column(String(5), default=None)

    # Origen del evento (web | app | totem | beacon | ...)
    canal: Mapped[str | None] = mapped_column(String(50), default=None, index=True)

    # Atributos específicos del evento (intención del chatbot, sección del tótem...)
    atributos: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_visitas_tipo_tiempo", "tipo", "ocurrido_en"),
    )
