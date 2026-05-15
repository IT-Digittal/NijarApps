"""Esquemas Pydantic para recursos, eventos y servicios turísticos."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from nijar_dti.schemas.common import GeoPoint, I18nText


# ---------------- Recurso Turístico ----------------

class RecursoTuristicoBase(BaseModel):
    urn: str = Field(..., pattern=r"^urn:ngsi-ld:RecursoTuristico:nijar:[a-z0-9-]+$")
    nombre: str = Field(..., max_length=255)
    categoria: str = Field(...,
        pattern=r"^(playa|monumento|ruta|mirador|centro_visitantes|"
                r"parque_natural|museo|yacimiento|punto_interes|oficina_turismo)$"
    )
    descripcion_corta: str | None = None
    nombre_i18n: I18nText | None = None
    descripcion_i18n: I18nText | None = None
    direccion: str | None = Field(default=None, max_length=500)
    municipio: str = "Níjar"
    codigo_postal: str | None = Field(default=None, pattern=r"^[0-9]{5}$")
    telefono: str | None = None
    email: EmailStr | None = None
    web: HttpUrl | None = None
    horario: dict | None = None
    accesibilidad: dict | None = None
    servicios_disponibles: list[str] | None = None
    etiquetas: list[str] | None = None
    imagenes: list[str] | None = None
    enlaces_externos: dict | None = None
    activo: bool = True
    publicado: bool = False


class RecursoTuristicoIn(RecursoTuristicoBase):
    ubicacion: GeoPoint | None = None


class RecursoTuristicoOut(RecursoTuristicoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ubicacion: GeoPoint | None = None
    created_at: datetime
    updated_at: datetime


class RecursoTuristicoFilter(BaseModel):
    categoria: str | None = None
    municipio: str | None = None
    publicado: bool | None = None
    cerca_de_lat: float | None = Field(default=None, ge=-90, le=90)
    cerca_de_lon: float | None = Field(default=None, ge=-180, le=180)
    radio_metros: int | None = Field(default=None, ge=1, le=100_000)


# ---------------- Evento Turístico ----------------

class EventoTuristicoBase(BaseModel):
    urn: str = Field(..., pattern=r"^urn:ngsi-ld:EventoTuristico:nijar:[a-z0-9-]+$")
    nombre: str = Field(..., max_length=255)
    tipo: str = Field(..., pattern=r"^(cultural|gastronomico|deportivo|musical|festivo|naturaleza|educativo|otro)$")
    descripcion: str | None = None
    nombre_i18n: I18nText | None = None
    descripcion_i18n: I18nText | None = None
    fecha_inicio: datetime
    fecha_fin: datetime
    recurso_id: UUID | None = None
    direccion: str | None = None
    organizador: str | None = None
    precio: str | None = None
    capacidad_aforo: int | None = Field(default=None, ge=0)
    enlace_inscripcion: HttpUrl | None = None
    imagenes: list[str] | None = None
    etiquetas: list[str] | None = None
    fuente: str | None = None
    activo: bool = True
    publicado: bool = False

    @field_validator("fecha_fin")
    @classmethod
    def fin_posterior_inicio(cls, v: datetime, info) -> datetime:
        inicio = info.data.get("fecha_inicio")
        if inicio and v < inicio:
            raise ValueError("fecha_fin debe ser igual o posterior a fecha_inicio")
        return v


class EventoTuristicoIn(EventoTuristicoBase):
    ubicacion: GeoPoint | None = None


class EventoTuristicoOut(EventoTuristicoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ubicacion: GeoPoint | None = None
    created_at: datetime
    updated_at: datetime


class EventoFilter(BaseModel):
    desde: datetime | None = None
    hasta: datetime | None = None
    tipo: str | None = None
    publicado: bool | None = None


# ---------------- Servicio ----------------

class ServicioBase(BaseModel):
    urn: str = Field(..., pattern=r"^urn:ngsi-ld:Servicio:nijar:[a-z0-9-]+$")
    nombre: str = Field(..., max_length=255)
    tipo: str = Field(...,
        pattern=r"^(alojamiento_hotel|alojamiento_apartamento|alojamiento_rural|"
                r"alojamiento_camping|gastronomia_restaurante|gastronomia_bar|"
                r"gastronomia_cafeteria|ocio_actividad|ocio_alquiler|transporte|"
                r"guia_turistico|comercio|otro)$"
    )
    descripcion: str | None = None
    nombre_i18n: I18nText | None = None
    descripcion_i18n: I18nText | None = None
    direccion: str | None = None
    municipio: str = "Níjar"
    codigo_postal: str | None = Field(default=None, pattern=r"^[0-9]{5}$")
    telefono: str | None = None
    email: EmailStr | None = None
    web: HttpUrl | None = None
    horario: dict | None = None
    rango_precios: str | None = None
    valoracion_media: float | None = Field(default=None, ge=0, le=5)
    registro_turismo: str | None = None
    cif: str | None = None
    accesibilidad: dict | None = None
    idiomas_atencion: list[str] | None = None
    etiquetas: list[str] | None = None
    imagenes: list[str] | None = None
    activo: bool = True
    publicado: bool = False


class ServicioIn(ServicioBase):
    ubicacion: GeoPoint | None = None


class ServicioOut(ServicioBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ubicacion: GeoPoint | None = None
    created_at: datetime
    updated_at: datetime


class ServicioFilter(BaseModel):
    tipo: str | None = None
    municipio: str | None = None
    publicado: bool | None = None
