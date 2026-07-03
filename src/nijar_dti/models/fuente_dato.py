"""Catálogo de fuentes de datos e integraciones de la plataforma DTI.

Identifica, para cada KPI, de dónde procede el dato: fuentes **propias**
(las genera directamente nuestra solución y las recogemos nosotros) frente a
fuentes **externas** (sistemas municipales o plataformas de terceros a las que
el Ayuntamiento debe facilitarnos acceso). Es el inventario que responde al
"Proyecto Actual: identificar las fuentes de datos, APIs y servicios que
deberán conectarse con la plataforma" y sirve de hoja de ruta de integración.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class OrigenFuente(StrEnum):
    """¿Quién genera / aporta el dato?"""

    PROPIA = "propia"  # La genera nuestra solución (la recogemos nosotros)
    EXTERNA = "externa"  # La aporta el Ayuntamiento / un tercero


class EstadoFuente(StrEnum):
    """Estado de disponibilidad/integración de la fuente."""

    OPERATIVA = "operativa"  # Ya integrada y fluyendo
    PENDIENTE_DESARROLLO = "pendiente_desarrollo"  # Depende de nosotros
    PENDIENTE_ACCESO = "pendiente_acceso"  # Depende de accesos del Ayuntamiento
    PLANIFICADA = "planificada"  # Prevista para una fase posterior


class FuenteDato(Base, TimestampMixin):
    """Una fuente de datos / integración de la plataforma."""

    __tablename__ = "fuentes_datos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # FD-001
    nombre: Mapped[str] = mapped_column(String(200))
    categoria: Mapped[str] = mapped_column(String(60), index=True)  # turismo, web_app, social...
    origen: Mapped[OrigenFuente] = mapped_column(String(20), index=True)
    estado: Mapped[EstadoFuente] = mapped_column(String(30), index=True)

    tipo_conexion: Mapped[str | None] = mapped_column(String(60), default=None)  # api_rest, mqtt...
    sistema: Mapped[str | None] = mapped_column(String(200), default=None)
    responsable: Mapped[str | None] = mapped_column(String(120), default=None)  # nosotros / ayto

    requiere_credenciales: Mapped[bool] = mapped_column(default=False)
    credenciales_desc: Mapped[str | None] = mapped_column(String(300), default=None)

    endpoint_url: Mapped[str | None] = mapped_column(String(300), default=None)
    periodicidad: Mapped[str | None] = mapped_column(String(60), default=None)
    formato: Mapped[str | None] = mapped_column(String(60), default=None)

    kpis_asociados: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    notas: Mapped[str | None] = mapped_column(Text, default=None)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)
