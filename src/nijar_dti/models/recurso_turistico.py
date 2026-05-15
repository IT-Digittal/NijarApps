"""Entidad RecursoTuristico — Recursos del destino Níjar.

Compatible con FIWARE Smart Data Models `PointOfInterest` y `TouristAttraction`.
Representa cualquier recurso de interés turístico georreferenciado: playas,
monumentos, rutas, miradores, centros de visitantes, etc.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class CategoriaRecurso(StrEnum):
    """Categorías de recurso turístico (vocabulario controlado)."""

    PLAYA = "playa"
    MONUMENTO = "monumento"
    RUTA = "ruta"
    MIRADOR = "mirador"
    CENTRO_VISITANTES = "centro_visitantes"
    PARQUE_NATURAL = "parque_natural"
    MUSEO = "museo"
    YACIMIENTO = "yacimiento"
    PUNTO_INTERES = "punto_interes"
    OFICINA_TURISMO = "oficina_turismo"


class RecursoTuristico(Base, AuditMixin):
    """Recurso turístico georreferenciado del destino Níjar."""

    __tablename__ = "recursos_turisticos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # Identificador URN único (FIWARE)
    # Formato: urn:ngsi-ld:RecursoTuristico:nijar:<slug>
    urn: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Descriptivo
    nombre: Mapped[str] = mapped_column(String(255), index=True)
    categoria: Mapped[CategoriaRecurso] = mapped_column(String(50), index=True)
    descripcion_corta: Mapped[str | None] = mapped_column(Text, default=None)

    # Multilingüe: {"es": "...", "en": "...", "de": "...", "fr": "..."}
    nombre_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)
    descripcion_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Geolocalización (PostGIS, WGS84)
    ubicacion: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        default=None,
    )

    # Dirección y contacto
    direccion: Mapped[str | None] = mapped_column(String(500), default=None)
    municipio: Mapped[str] = mapped_column(String(100), default="Níjar")
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)
    telefono: Mapped[str | None] = mapped_column(String(50), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    web: Mapped[str | None] = mapped_column(String(500), default=None)

    # Atributos turísticos
    horario: Mapped[dict | None] = mapped_column(JSON, default=None)
    accesibilidad: Mapped[dict | None] = mapped_column(JSON, default=None)
    servicios_disponibles: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=None
    )
    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    # Multimedia y enlaces
    imagenes: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    enlaces_externos: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Estado y visibilidad
    activo: Mapped[bool] = mapped_column(default=True)
    publicado: Mapped[bool] = mapped_column(default=False)

    # Metadatos extensibles para futuras integraciones
    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_recursos_categoria_activo", "categoria", "activo"),
        Index("ix_recursos_ubicacion_gist", "ubicacion", postgresql_using="gist"),
    )
