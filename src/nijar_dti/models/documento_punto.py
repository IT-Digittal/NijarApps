"""Documentos adjuntos a los puntos del territorio (gemelo digital).

Cualquier activo georreferenciado del gemelo (recurso turístico, sensor,
cuadro de alumbrado, contenedor, punto de movilidad, cámara, bandera de playa,
estación de aire…) puede llevar documentos asociados: fichas técnicas, fotos,
planos, contratos de mantenimiento… El fichero vive en el almacenamiento de la
plataforma (``STORAGE_LOCAL_PATH``); aquí solo se guardan los metadatos y la
referencia de la entidad (tipo + identificador + nombre y coordenadas
desnormalizados, para poder listar y pintar sin joins por cada vertical).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class DocumentoPunto(Base, TimestampMixin):
    """Un documento adjunto a un punto del mapa."""

    __tablename__ = "documentos_puntos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # Referencia de la entidad (capa del gemelo + identificador dentro de ella)
    entidad_tipo: Mapped[str] = mapped_column(String(30), index=True)
    entidad_id: Mapped[str] = mapped_column(String(255), index=True)
    entidad_nombre: Mapped[str] = mapped_column(String(255))
    latitud: Mapped[float | None] = mapped_column(Float, default=None)
    longitud: Mapped[float | None] = mapped_column(Float, default=None)

    # Metadatos del fichero (el binario vive en el almacenamiento)
    nombre_archivo: Mapped[str] = mapped_column(String(255), default="")
    descripcion: Mapped[str | None] = mapped_column(String(500), default=None)
    tipo_mime: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    tamano_bytes: Mapped[int] = mapped_column(Integer, default=0)
    ruta_almacen: Mapped[str] = mapped_column(String(500), default="")

    subido_por: Mapped[str | None] = mapped_column(String(255), default=None)

    __table_args__ = (Index("ix_documentos_entidad", "entidad_tipo", "entidad_id"),)
