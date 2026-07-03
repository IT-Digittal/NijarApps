"""Esquemas del catálogo de fuentes de datos e integraciones."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FuenteDatoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    categoria: str
    origen: str
    estado: str
    tipo_conexion: str | None = None
    sistema: str | None = None
    responsable: str | None = None
    requiere_credenciales: bool
    credenciales_desc: str | None = None
    periodicidad: str | None = None
    formato: str | None = None
    kpis_asociados: list[str] | None = None
    notas: str | None = None


class FuentesResumen(BaseModel):
    total: int
    propias: int
    externas: int
    operativas: int
    pendiente_desarrollo: int
    pendiente_acceso: int
    requieren_credenciales: int
    por_categoria: dict[str, int]
    por_estado: dict[str, int]
