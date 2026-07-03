"""Esquemas de las verticales Smart City (overview de KPIs + activos)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Paginado(BaseModel):
    total: int
    page: int
    page_size: int


# ----------------------------------------------------------------- ALUMBRADO
class ZonaAlumbradoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nombre: str
    luminarias: int
    led: int
    vsap: int
    solar: int
    latitud: float | None = None
    longitud: float | None = None


class CuadroMandoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    zona_id: str
    ubicacion: str | None = None
    circuitos: int
    potencia_kw: float
    comunicaciones: str
    sla: int
    estado: str
    alarmas: list[str] | None = None


class LuminariaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    zona_id: str
    cuadro_codigo: str | None = None
    circuito: str | None = None
    direccion: str | None = None
    tecnologia: str
    potencia_w: int
    marca_modelo: str | None = None
    anio_instalacion: int | None = None
    estado: str
    nivel_regulacion: int
    horas_funcionamiento: int | None = None
    consumo_mes_kwh: float | None = None
    ultima_comunicacion_min: int | None = None
    latitud: float | None = None
    longitud: float | None = None


class LuminariasPage(Paginado):
    items: list[LuminariaOut]


class AlumbradoOverview(BaseModel):
    total_luminarias: int
    led: int
    vsap: int
    solar: int
    pct_led: float
    operativas: int
    en_averia: int
    sin_comunicacion: int
    disponibilidad_pct: float
    cuadros_total: int
    cuadros_online: int
    cuadros_alerta: int
    circuitos_total: int
    potencia_instalada_kw: float
    consumo_mes_kwh: float
    ahorro_energetico_pct: float
    incidencias_abiertas: int
    zonas: list[ZonaAlumbradoOut]


# ---------------------------------------------------------------------- AGUA
class SectorAguaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    contadores: int
    contadores_telelectura: int
    caudal_entrada_ls: float
    presion_bar: float | None = None
    rendimiento_pct: float | None = None
    fugas_detectadas: int
    estado: str


class AguaOverview(BaseModel):
    sectores: int
    contadores: int
    contadores_telelectura: int
    pct_telelectura: float
    caudal_total_ls: float
    fugas_detectadas: int
    rendimiento_medio_pct: float
    sectores_en_alerta: int
    detalle: list[SectorAguaOut]


# ------------------------------------------------------------------ RESIDUOS
class ContenedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    zona_id: str
    fraccion: str
    tiene_sensor: bool
    llenado_pct: int | None = None
    ruta: str | None = None
    estado: str


class ContenedoresPage(Paginado):
    items: list[ContenedorOut]


class ResiduosOverview(BaseModel):
    total: int
    con_sensor: int
    pct_sensor: float
    llenado_alto: int  # ≥ 80 %
    llenado_medio_pct: float
    rutas: int
    por_fraccion: dict[str, int]


# ----------------------------------------------------------------- MOVILIDAD
class PuntoMovilidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    tipo: str
    ubicacion: str | None = None
    valor_actual: int | None = None
    capacidad: int | None = None
    unidad: str | None = None
    estado: str


class MovilidadOverview(BaseModel):
    puntos: int
    aforos: int
    trafico_actual_veh_h: int
    parkings: int
    plazas_totales: int
    plazas_ocupadas: int
    ocupacion_parking_pct: float
    puntos_recarga_ev: int
    tomas_ev_libres: int
    detalle: list[PuntoMovilidadOut]


# ----------------------------------------------------------------- SEGURIDAD
class CamaraCCTVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    zona_id: str
    tipo: str | None = None
    con_analitica: bool
    retencion_dias: int
    estado: str


class SeguridadOverview(BaseModel):
    camaras: int
    online: int
    sin_comunicacion: int
    pct_online: float
    con_analitica: int
    retencion_dias: int
    detalle: list[CamaraCCTVOut]


# ------------------------------------------------------------------- ENERGÍA
class SuministroEnergiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cups: str
    edificio: str
    tipo: str | None = None
    potencia_contratada_kw: float
    consumo_mes_kwh: float
    autoconsumo_mes_kwh: float
    coste_mes_eur: float
    tiene_fotovoltaica: bool
    estado: str


class SuministrosPage(Paginado):
    items: list[SuministroEnergiaOut]


class EnergiaOverview(BaseModel):
    cups: int
    edificios: int
    consumo_mes_kwh: float
    autoconsumo_mes_kwh: float
    autoconsumo_pct: float
    coste_mes_eur: float
    cups_con_fotovoltaica: int
    coste_medio_kwh: float
