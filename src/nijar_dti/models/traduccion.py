"""Caché de traducciones automáticas de contenidos para el tótem.

Los avisos del CMS, las noticias y la agenda cultural de la web municipal se
publican solo en español. Se traducen con IA la primera vez que un visitante
los pide en otro idioma y la traducción se guarda aquí: cada texto se traduce
una sola vez por idioma (la clave es un hash de idioma + texto de origen).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base


class Traduccion(Base):
    """Traducción de un texto de origen (español) a un idioma del tótem."""

    __tablename__ = "traducciones"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    clave: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    idioma: Mapped[str] = mapped_column(String(5))
    texto_origen: Mapped[str] = mapped_column(Text)
    texto_traducido: Mapped[str] = mapped_column(Text)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
