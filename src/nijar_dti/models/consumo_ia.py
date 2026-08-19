"""Registro de consumo de modelos de IA generativa (control de costes).

Cada llamada a un proveedor de IA (hoy OpenAI desde el chatbot; mañana
cualquier otro punto de la plataforma que use IA) deja una fila con los
tokens consumidos, el modelo y el coste estimado, de modo que el panel
pueda mostrar el gasto por servicio, canal y día.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base


class ConsumoIA(Base):
    """Una llamada facturable a un modelo de IA."""

    __tablename__ = "consumos_ia"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    proveedor: Mapped[str] = mapped_column(String(30), default="openai")
    modelo: Mapped[str] = mapped_column(String(80), default="")
    servicio: Mapped[str] = mapped_column(String(60), default="chatbot")
    canal: Mapped[str] = mapped_column(String(30), default="")
    idioma: Mapped[str | None] = mapped_column(String(5), default=None)
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0)
    tokens_salida: Mapped[int] = mapped_column(Integer, default=0)
    coste_estimado_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latencia_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    interaccion_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), default=None)
