"""Entidad Opinion — Menciones del destino en redes sociales y reseñas.

Almacena las menciones capturadas por el motor de Social Listening
(X, Facebook, Instagram, TripAdvisor) junto con su análisis NLP.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class FuenteOpinion(StrEnum):
    """Plataformas de origen."""

    TWITTER_X = "twitter_x"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TRIPADVISOR = "tripadvisor"
    GOOGLE_REVIEWS = "google_reviews"
    ENCUESTA_MUNICIPAL = "encuesta_municipal"
    OTRO = "otro"


class Sentimiento(StrEnum):
    """Etiqueta de sentimiento."""

    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"
    DESCONOCIDO = "desconocido"


class Opinion(Base, TimestampMixin):
    """Mención u opinión sobre el destino capturada por Social Listening."""

    __tablename__ = "opiniones"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # ---- Campos obligatorios (sin default) ----
    fuente: Mapped[FuenteOpinion] = mapped_column(String(40), index=True)
    texto_original: Mapped[str] = mapped_column(Text)
    publicado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ---- Campos con default ----
    fuente_id_externo: Mapped[str | None] = mapped_column(String(255), index=True, default=None)
    autor_handle: Mapped[str | None] = mapped_column(String(255), default=None)
    idioma: Mapped[str | None] = mapped_column(String(5), index=True, default=None)

    # Análisis NLP
    sentimiento: Mapped[Sentimiento] = mapped_column(
        String(20), default=Sentimiento.DESCONOCIDO, index=True
    )
    score_sentimiento: Mapped[float | None] = mapped_column(Numeric(5, 4), default=None)
    temas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    entidades_mencionadas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    # Métricas de interacción de la publicación original
    metricas: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Geolocalización si está disponible
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)

    # Trazabilidad / linaje
    capturado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    payload_original: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Validación humana (revisión QA modelo NLP)
    revisado_humano: Mapped[bool] = mapped_column(default=False)
    sentimiento_humano: Mapped[Sentimiento | None] = mapped_column(String(20), default=None)

    __table_args__ = (
        Index("ix_opiniones_fuente_publicado", "fuente", "publicado_en"),
        Index("ix_opiniones_sentimiento_publicado", "sentimiento", "publicado_en"),
    )
