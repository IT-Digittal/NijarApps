"""Entidad FAQ — Base de conocimiento del chatbot IA."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class NivelConfianza(StrEnum):
    """Niveles de confianza de las fuentes del chatbot."""

    ALTA = "alta"
    MEDIA = "media"
    FUERA_DE_DOMINIO = "fuera_de_dominio"


class FAQ(Base, AuditMixin):
    """Pareja intent → respuesta con grounding multilingüe."""

    __tablename__ = "faqs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- campos obligatorios ----
    intent: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    categoria: Mapped[str] = mapped_column(String(50), index=True)
    pregunta_es: Mapped[str] = mapped_column(Text)
    respuesta_es: Mapped[str] = mapped_column(Text)

    # ---- campos opcionales con default ----
    pregunta_en: Mapped[str | None] = mapped_column(Text, default=None)
    pregunta_de: Mapped[str | None] = mapped_column(Text, default=None)
    pregunta_fr: Mapped[str | None] = mapped_column(Text, default=None)

    frases_entrenamiento_es: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    frases_entrenamiento_en: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    frases_entrenamiento_de: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    frases_entrenamiento_fr: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    respuesta_en: Mapped[str | None] = mapped_column(Text, default=None)
    respuesta_de: Mapped[str | None] = mapped_column(Text, default=None)
    respuesta_fr: Mapped[str | None] = mapped_column(Text, default=None)

    nivel_confianza: Mapped[NivelConfianza] = mapped_column(String(20), default=NivelConfianza.ALTA)
    fuente_url: Mapped[str | None] = mapped_column(String(500), default=None)
    fuente_descripcion: Mapped[str | None] = mapped_column(String(255), default=None)
    fecha_validez_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    activo: Mapped[bool] = mapped_column(default=True)
    version: Mapped[int] = mapped_column(default=1)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (Index("ix_faqs_categoria_activo", "categoria", "activo"),)


class InteraccionChatbot(Base, AuditMixin):
    """Registro de cada interacción usuario-chatbot para telemetría y mejora."""

    __tablename__ = "interacciones_chatbot"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- obligatorios ----
    sesion_id: Mapped[str] = mapped_column(String(100), index=True)
    canal: Mapped[str] = mapped_column(String(20), index=True)
    idioma: Mapped[str] = mapped_column(String(5))
    pregunta: Mapped[str] = mapped_column(Text)
    respuesta: Mapped[str] = mapped_column(Text)

    # ---- opcionales con default ----
    intent_detectado: Mapped[str | None] = mapped_column(String(100), default=None, index=True)
    nivel_confianza: Mapped[str] = mapped_column(String(20), default="fuera_de_dominio")
    score_confianza: Mapped[float | None] = mapped_column(default=None)
    fuentes: Mapped[list[dict] | None] = mapped_column(JSON, default=None)
    util: Mapped[bool | None] = mapped_column(default=None)
    comentario: Mapped[str | None] = mapped_column(Text, default=None)
    latencia_ms: Mapped[int | None] = mapped_column(default=None)

    __table_args__ = (
        Index("ix_interacciones_sesion_creado", "sesion_id", "created_at"),
        Index("ix_interacciones_intent_creado", "intent_detectado", "created_at"),
    )
