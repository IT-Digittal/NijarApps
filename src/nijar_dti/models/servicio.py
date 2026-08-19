"""Entidad Servicio — Empresas y servicios turísticos del destino.

Compatible con FIWARE Smart Data Models del sector turístico.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import AuditMixin


class TipoServicio(StrEnum):
    """Tipologías de servicio turístico."""

    ALOJAMIENTO_HOTEL = "alojamiento_hotel"
    ALOJAMIENTO_APARTAMENTO = "alojamiento_apartamento"
    ALOJAMIENTO_RURAL = "alojamiento_rural"
    ALOJAMIENTO_CAMPING = "alojamiento_camping"
    GASTRONOMIA_RESTAURANTE = "gastronomia_restaurante"
    GASTRONOMIA_BAR = "gastronomia_bar"
    GASTRONOMIA_CAFETERIA = "gastronomia_cafeteria"
    OCIO_ACTIVIDAD = "ocio_actividad"
    OCIO_ALQUILER = "ocio_alquiler"
    TRANSPORTE = "transporte"
    GUIA_TURISTICO = "guia_turistico"
    COMERCIO = "comercio"
    OTRO = "otro"


class Servicio(Base, AuditMixin):
    """Servicio turístico ofrecido en el destino."""

    __tablename__ = "servicios"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    urn: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    tipo: Mapped[TipoServicio] = mapped_column(String(50), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)

    nombre_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)
    descripcion_i18n: Mapped[dict | None] = mapped_column(JSON, default=None)

    ubicacion: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        default=None,
    )

    direccion: Mapped[str | None] = mapped_column(String(500), default=None)
    municipio: Mapped[str] = mapped_column(String(100), default="Níjar")
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)

    telefono: Mapped[str | None] = mapped_column(String(50), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    web: Mapped[str | None] = mapped_column(String(500), default=None)

    horario: Mapped[dict | None] = mapped_column(JSON, default=None)
    rango_precios: Mapped[str | None] = mapped_column(String(20), default=None)
    valoracion_media: Mapped[float | None] = mapped_column(Numeric(3, 2), default=None)

    # Identificadores oficiales (registro de turismo, NIF, etc.)
    registro_turismo: Mapped[str | None] = mapped_column(String(100), default=None)
    cif: Mapped[str | None] = mapped_column(String(20), default=None)

    accesibilidad: Mapped[dict | None] = mapped_column(JSON, default=None)
    idiomas_atencion: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    etiquetas: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    imagenes: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)

    activo: Mapped[bool] = mapped_column(default=True)
    publicado: Mapped[bool] = mapped_column(default=False)

    metadata_adicional: Mapped[dict | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("ix_servicios_tipo_activo", "tipo", "activo"),
        Index("ix_servicios_ubicacion_gist", "ubicacion", postgresql_using="gist"),
    )
