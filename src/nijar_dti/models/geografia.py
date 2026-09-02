"""Capas geográficas del Gemelo vivo 2D — catálogo de capas vectoriales.

Modela la cartografía por capas del gemelo digital al estilo de un geoportal
municipal de urbanismo (clasificación y calificación del suelo, ordenación
estructural, partidos rurales, parcelario catastral…). Cada capa es un
conjunto de elementos vectoriales (polígonos, líneas o puntos) que el frontend
pinta y conmuta de forma independiente.

Diseño genérico a propósito:
- `CapaGeografica` es el catálogo (una fila por capa: nombre, grupo, estilo…).
- `ElementoGeografico` son los rasgos (geometría PostGIS + propiedades JSON).

Así, cuando el Ayuntamiento aporte los datos reales del PGOU o los registros
catastrales, se cargan como filas de estas tablas sin tocar el esquema. El
campo `referencia_catastral` deja preparada la vinculación de cada parcela con
los registros de catastro que se integrarán más adelante.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class GrupoCapa(StrEnum):
    """Agrupación temática de las capas en el control del mapa."""

    PLANEAMIENTO = "planeamiento"
    CATASTRO = "catastro"
    CLASIFICACION = "clasificacion"
    OTRAS = "otras"


class TipoGeometria(StrEnum):
    """Tipo geométrico predominante de una capa (para estilo y validación)."""

    POLIGONO = "poligono"
    LINEA = "linea"
    PUNTO = "punto"


class CapaGeografica(Base, TimestampMixin):
    """Definición de una capa vectorial del gemelo (catálogo)."""

    __tablename__ = "capas_geograficas"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    # Identificador estable y legible usado por la API y el frontend
    codigo: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    grupo: Mapped[GrupoCapa] = mapped_column(String(30), index=True)
    tipo_geometria: Mapped[TipoGeometria] = mapped_column(String(20))

    descripcion: Mapped[str | None] = mapped_column(Text, default=None)

    # Estilo por defecto (el frontend puede sobrescribirlo)
    color: Mapped[str] = mapped_column(String(9), default="#7C6BF0")
    color_borde: Mapped[str] = mapped_column(String(9), default="#3A2FA0")
    opacidad: Mapped[float] = mapped_column(Float, default=0.35)

    # Nombre de la propiedad usada como etiqueta principal en el popup
    campo_etiqueta: Mapped[str | None] = mapped_column(String(80), default=None)

    orden: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    # Procedencia del dato (organismo, expediente, «demostración», etc.)
    fuente: Mapped[str | None] = mapped_column(String(255), default=None)

    metadatos: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class ElementoGeografico(Base, TimestampMixin):
    """Rasgo vectorial (polígono/línea/punto) perteneciente a una capa."""

    __tablename__ = "elementos_geograficos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    capa_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("capas_geograficas.id", ondelete="CASCADE"),
        index=True,
    )

    nombre: Mapped[str] = mapped_column(String(255))

    # Geometría genérica en WGS84 (admite POLYGON/MULTIPOLYGON/LINESTRING/POINT).
    # Se escribe como WKTElement; en las consultas solo se opera vía funciones
    # ST_* de PostGIS, nunca leyendo el atributo en Python.
    geometria: Mapped[WKTElement | str] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
    )

    codigo: Mapped[str | None] = mapped_column(String(120), default=None)

    # Referencia catastral (20 dígitos). Deja preparada la vinculación con los
    # registros de catastro que se integrarán más adelante.
    referencia_catastral: Mapped[str | None] = mapped_column(String(20), index=True, default=None)

    # Atributos temáticos libres: uso, calificación, clasificación de suelo,
    # superficie, aprovechamiento, etc.
    propiedades: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    orden: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("ix_elementos_geograficos_capa", "capa_id", "orden"),)


class TipoMedicion(StrEnum):
    """Forma de una medición guardada de la regla del gemelo."""

    LINEA = "linea"
    POLIGONO = "poligono"


class MedicionGemelo(Base, TimestampMixin):
    """Medición guardada desde la regla del Gemelo vivo 2D.

    Los vértices se guardan como lista ``[[lat, lon], ...]`` en WGS84; la
    distancia (y el área si es polígono) las calcula el backend a partir de
    los puntos al guardar, para que el dato almacenado sea siempre coherente.
    """

    __tablename__ = "mediciones_gemelo"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default_factory=uuid4,
        init=False,
    )

    nombre: Mapped[str] = mapped_column(String(150))
    tipo: Mapped[TipoMedicion] = mapped_column(String(10))

    # Vértices [[lat, lon], ...] en WGS84
    puntos: Mapped[list[Any]] = mapped_column(JSON)

    distancia_m: Mapped[float] = mapped_column(Float)
    area_m2: Mapped[float | None] = mapped_column(Float, default=None)

    # Email del usuario que la guardó (para permitir que borre las suyas)
    creado_por: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
