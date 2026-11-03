"""Esquemas de las verticales Smart City (overview de KPIs + activos)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

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
    latitud: float | None = None
    longitud: float | None = None


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
    otras: int = 0  # halogenuro metálico o tecnología sin dato en el inventario
    # False si el inventario es real (WeLight) pero aún sin telegestión: estados,
    # averías y comunicaciones no se conocen todavía.
    telemetria: bool = True
    fuente_inventario: str | None = None  # "welight" | None (inventario de demostración)


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
    latitud: float | None = None
    longitud: float | None = None


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
    latitud: float | None = None
    longitud: float | None = None


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
    latitud: float | None = None
    longitud: float | None = None


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


# ---------------- Datadis (consumo eléctrico) ----------------


class EnergiaDiaMunicipio(BaseModel):
    fecha: date
    energia_kwh: float
    contratos: int
    sectores: dict[str, float]  # kWh por sector económico


class EnergiaMunicipioSerie(BaseModel):
    """Consumo eléctrico de todo el municipio (Datadis, datos públicos)."""

    fuente: str = "datadis"
    desde: date
    hasta: date
    ultima_fecha_disponible: date | None
    energia_total_kwh: float
    contratos_ultimo_dia: int | None
    por_sector_kwh: dict[str, float]
    serie: list[EnergiaDiaMunicipio]


class LecturaHorariaOut(BaseModel):
    momento: datetime
    consumo_kwh: float
    autoconsumo_kwh: float | None
    excedente_kwh: float | None
    metodo: str | None


class EstadoDatadis(BaseModel):
    publico_activo: bool
    privado_configurado: bool
    ultima_fecha_publica: date | None
    dias_publicos_cargados: int
    suministros_reales: int
    ultima_lectura_privada: datetime | None


class ImportacionDatadisOut(BaseModel):
    """Resultado de importar el fichero descargado de datadis.es."""

    fichero: str
    filas: int
    guardadas: int
    otros_municipios: int
    no_interpretables: int
    desde: date | None
    hasta: date | None


# ------------------------------------------- ENERGÍA MUNICIPAL (Datadis real)
class MesConsumoEnergia(BaseModel):
    periodo: str  # AAAA-MM
    kwh: float
    alumbrado_kwh: float = 0.0
    edificios_kwh: float = 0.0
    completo: bool = True  # False = mes en curso o con días sin lectura


class SuministroAnalisis(BaseModel):
    """Un CUPS municipal con su consumo real y el análisis de su contrato."""

    cups: str
    direccion: str
    tipo: str  # "alumbrado" | "edificio"
    tarifa: str | None = None
    potencia_contratada_kw: float | None = None
    consumo_mes_kwh: float = 0.0
    consumo_mes_anterior_kwh: float = 0.0
    variacion_mes_pct: float | None = None
    consumo_mismo_mes_anio_anterior_kwh: float | None = None
    variacion_interanual_pct: float | None = None
    consumo_12m_kwh: float = 0.0
    coste_mes_eur: float = 0.0
    pico_horario_kw: float | None = None  # mayor consumo en una hora (≈ kW medios de esa hora)
    pico_momento: datetime | None = None
    utilizacion_pct: float | None = None  # pico horario / potencia contratada
    potencia_recomendada_kw: float | None = None
    ahorro_potencia_eur_anio: float | None = None
    autoconsumo_12m_kwh: float = 0.0
    excedente_12m_kwh: float = 0.0
    ultima_lectura: datetime | None = None
    dias_sin_lectura: int | None = None
    meses_con_datos: int = 0
    estado: str = "ok"  # ok | sin_datos_recientes | sin_datos


class RecomendacionEnergia(BaseModel):
    prioridad: str  # alta | media | informativa
    titulo: str
    detalle: str
    cups: list[str] = []
    ahorro_eur_anio: float | None = None


class ResumenEnergiaMunicipal(BaseModel):
    hay_datos: bool
    periodo: str | None = None  # último mes cerrado analizado
    suministros_total: int = 0
    suministros_con_datos: int = 0
    suministros_alumbrado: int = 0
    suministros_edificios: int = 0
    consumo_mes_kwh: float = 0.0
    consumo_mes_alumbrado_kwh: float = 0.0
    consumo_mes_edificios_kwh: float = 0.0
    variacion_mes_pct: float | None = None
    variacion_interanual_pct: float | None = None
    coste_mes_eur: float = 0.0
    precio_kwh_eur: float = 0.0
    co2_mes_t: float = 0.0
    consumo_12m_kwh: float = 0.0
    coste_12m_eur: float = 0.0
    potencia_contratada_total_kw: float = 0.0
    contratos_a_revisar: int = 0
    ahorro_potencia_eur_anio: float = 0.0
    autoconsumo_12m_kwh: float = 0.0
    excedente_12m_kwh: float = 0.0
    cups_con_autoconsumo: int = 0
    sin_datos_recientes: int = 0
    ultima_lectura: datetime | None = None
    serie_mensual: list[MesConsumoEnergia] = []
    por_tarifa: dict[str, int] = {}
    top_consumo: list[SuministroAnalisis] = []
    recomendaciones: list[RecomendacionEnergia] = []
    notas: list[str] = []


class DetalleSuministroEnergia(BaseModel):
    suministro: SuministroAnalisis
    contrato: dict[str, Any] = {}
    distribuidora: str | None = None
    codigo_postal: str | None = None
    serie_mensual: list[MesConsumoEnergia] = []
    perfil_horario_kwh: list[float] = []  # consumo medio por hora del día (0-23), últimos 30 días
    perfil_laborable_kwh: list[float] = []
    perfil_festivo_kwh: list[float] = []


# -------------------------------------------------- REGISTROS DE LAS VERTICALES
class RegistroVerticalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    vertical: str
    tipo: str
    severidad: str
    mensaje: str
    momento: datetime
    activo_codigo: str | None = None
    activo_nombre: str | None = None
    origen: str
    datos: dict[str, Any] | None = None
    demo: bool = False


class RegistrosPage(BaseModel):
    items: list[RegistroVerticalOut]
    total: int
    page: int
    page_size: int


class ResumenRegistros(BaseModel):
    vertical: str
    ultimas_24h: int
    criticos_24h: int
    avisos_24h: int
    ultimos_7d: int
    por_tipo_7d: dict[str, int]
    ultimo: datetime | None = None
    total: int
    solo_demo: bool
