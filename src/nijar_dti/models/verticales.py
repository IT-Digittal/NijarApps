"""Verticales Smart City transversales (agua, residuos, movilidad,
seguridad y energía).

Cada vertical reutiliza el mismo modelo troncal de la plataforma DTI
(municipio → zona → instalación → activo → incidencia → informe). Aquí se
definen los activos mínimos de cada vertical que alimentan sus KPIs.
"""

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from nijar_dti.core.database import Base
from nijar_dti.models._mixins import TimestampMixin


class EstadoVertical(StrEnum):
    OPERATIVO = "operativo"
    ALERTA = "alerta"
    AVERIA = "averia"
    SIN_COMUNICACION = "sin_comunicacion"


# --------------------------------------------------------------------- AGUA
class SectorAgua(Base, TimestampMixin):
    """Sector hidráulico (DMA) con telelectura y balance de caudal."""

    __tablename__ = "agua_sectores"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # SEC-01
    nombre: Mapped[str] = mapped_column(String(120))
    contadores: Mapped[int] = mapped_column(default=0)
    contadores_telelectura: Mapped[int] = mapped_column(default=0)
    caudal_entrada_ls: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    caudal_nocturno_ls: Mapped[float | None] = mapped_column(Numeric(8, 2), default=None)
    presion_bar: Mapped[float | None] = mapped_column(Numeric(4, 2), default=None)
    rendimiento_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), default=None)
    fugas_detectadas: Mapped[int] = mapped_column(default=0)
    estado: Mapped[EstadoVertical] = mapped_column(
        String(30), default=EstadoVertical.OPERATIVO, index=True
    )
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)


# ----------------------------------------------------------------- RESIDUOS
class FraccionResiduo(StrEnum):
    ORGANICA = "organica"
    ENVASES = "envases"
    PAPEL = "papel"
    VIDRIO = "vidrio"
    RESTO = "resto"


class Contenedor(Base, TimestampMixin):
    """Contenedor de residuos (con o sin sensor de llenado)."""

    __tablename__ = "residuos_contenedores"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # RSU-0001
    zona_id: Mapped[str] = mapped_column(String(40), index=True)
    fraccion: Mapped[FraccionResiduo] = mapped_column(String(20), index=True)
    tiene_sensor: Mapped[bool] = mapped_column(default=False, index=True)
    llenado_pct: Mapped[int | None] = mapped_column(default=None)
    ruta: Mapped[str | None] = mapped_column(String(40), default=None)
    estado: Mapped[EstadoVertical] = mapped_column(String(30), default=EstadoVertical.OPERATIVO)
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)

    __table_args__ = (Index("ix_contenedores_zona_fraccion", "zona_id", "fraccion"),)


# ---------------------------------------------------------------- MOVILIDAD
class TipoMovilidad(StrEnum):
    AFORO = "aforo"
    PARKING = "parking"
    RECARGA_EV = "recarga_ev"
    LANZADERA = "lanzadera"


class PuntoMovilidad(Base, TimestampMixin):
    """Punto de movilidad: aforo de acceso, aparcamiento, recarga o lanzadera."""

    __tablename__ = "movilidad_puntos"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # MOV-01
    nombre: Mapped[str] = mapped_column(String(160))
    tipo: Mapped[TipoMovilidad] = mapped_column(String(20), index=True)
    ubicacion: Mapped[str | None] = mapped_column(String(200), default=None)
    valor_actual: Mapped[int | None] = mapped_column(default=None)  # vehículos/plazas/kw
    capacidad: Mapped[int | None] = mapped_column(default=None)
    unidad: Mapped[str | None] = mapped_column(String(30), default=None)
    estado: Mapped[EstadoVertical] = mapped_column(String(30), default=EstadoVertical.OPERATIVO)
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)


# ---------------------------------------------------------------- SEGURIDAD
class CamaraCCTV(Base, TimestampMixin):
    """Cámara de videovigilancia CCTV integrada con Policía Local."""

    __tablename__ = "seguridad_camaras"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CCTV-01
    nombre: Mapped[str] = mapped_column(String(160))
    zona_id: Mapped[str] = mapped_column(String(40), index=True)
    tipo: Mapped[str | None] = mapped_column(String(40), default=None)  # fija/domo/lpr
    con_analitica: Mapped[bool] = mapped_column(default=False)
    retencion_dias: Mapped[int] = mapped_column(default=30)
    estado: Mapped[EstadoVertical] = mapped_column(
        String(30), default=EstadoVertical.OPERATIVO, index=True
    )
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), default=None)


# ------------------------------------------------------------------ ENERGÍA
class SuministroEnergia(Base, TimestampMixin):
    """Punto de suministro eléctrico municipal (CUPS) telemedido."""

    __tablename__ = "energia_suministros"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    cups: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    edificio: Mapped[str] = mapped_column(String(160), index=True)
    tipo: Mapped[str | None] = mapped_column(String(60), default=None)  # dependencia/alumbrado
    potencia_contratada_kw: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    consumo_mes_kwh: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    autoconsumo_mes_kwh: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    coste_mes_eur: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tiene_fotovoltaica: Mapped[bool] = mapped_column(default=False)
    estado: Mapped[EstadoVertical] = mapped_column(String(30), default=EstadoVertical.OPERATIVO)
    metadatos: Mapped[dict | None] = mapped_column(JSON, default=None)
