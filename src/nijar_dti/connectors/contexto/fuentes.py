"""Conectores concretos de fuentes públicas oficiales.

Implementan el patrón del proyecto: ruta real (``oficiales.py``, ``httpx``)
cuando ``dry_run`` es False y datos sintéticos coherentes cuando es True. Las
series sintéticas reproducen la estacionalidad estival de Almería/Cabo de Gata
y llevan ``metadatos["sintetico"] = True`` para que la Vista de Gobierno las
etiquete como demostración; los datos reales nunca llevan esa marca.

Fuentes reales (acceso libre, sin credenciales):

==================  ===========================================  ==================
conector            serie                                        origen
==================  ===========================================  ==================
ine_eoh             pernoctaciones hoteleras, prov. Almería      INE EOH · EOT1460
ine_frontur         turistas internacionales, Andalucía          INE FRONTUR · FREG351
ine_egatur          gasto de turistas internacionales, Andalucía INE EGATUR · FREG537
junta_andalucia     viajeros en hoteles, prov. Almería           IECA (BADEA) · 8035
aena                pasajeros del aeropuerto de Almería (LEI)    Excel mensual de AENA
==================  ===========================================  ==================
"""

from __future__ import annotations

from datetime import date

from nijar_dti.connectors.contexto import oficiales
from nijar_dti.connectors.contexto.base import (
    ContextoRecord,
    FuentePublicaConnector,
)

# Patrón de estacionalidad mensual (índice 1.0 = media anual) del litoral de
# Cabo de Gata: pico junio-septiembre, valle invernal.
_ESTACIONALIDAD = [0.45, 0.50, 0.70, 0.95, 1.20, 1.55, 1.95, 1.95, 1.35, 0.90, 0.55, 0.45]


def _periodos_mensuales(anios: int, ref: date | None = None) -> list[tuple[str, int]]:
    """Lista de ``("AAAA-MM", mes)`` para los últimos ``anios`` años cerrados."""
    ref = ref or date.today()
    salida: list[tuple[str, int]] = []
    # arranca en enero de (año_ref - anios) y termina en el mes anterior al ref
    for offset in range(anios * 12, 0, -1):
        total = (ref.year * 12 + (ref.month - 1)) - offset
        anio, mes0 = divmod(total, 12)
        mes = mes0 + 1
        salida.append((f"{anio:04d}-{mes:02d}", mes))
    return salida


def _serie_mensual_sintetica(base_anual_media: float, anios: int) -> list[tuple[str, float]]:
    """Genera una serie mensual sintética con estacionalidad y leve tendencia."""
    out: list[tuple[str, float]] = []
    periodos = _periodos_mensuales(anios)
    n = len(periodos)
    for i, (periodo, mes) in enumerate(periodos):
        # tendencia suave de recuperación post-pandemia (+ ~3%/año)
        tendencia = 1.0 + 0.03 * ((i - n) / 12)
        valor = base_anual_media * _ESTACIONALIDAD[mes - 1] * max(tendencia, 0.6)
        out.append((periodo, round(valor, 2)))
    return out


def _anios_naturales(anios: int, ref: date | None = None) -> list[int]:
    """Años naturales que cubren los últimos ``anios`` años hasta hoy."""
    ref = ref or date.today()
    return list(range(ref.year - anios, ref.year + 1))


def _meta(base: dict, punto: oficiales.PuntoMensual | None = None, **extra) -> dict:
    meta = {**base, **extra}
    if punto is not None and punto.provisional:
        meta["provisional"] = True
    return meta


class INEFronturConnector(FuentePublicaConnector):
    """Turismo internacional (Frontur) — INE, mensual, ámbito Andalucía."""

    fuente = "ine_frontur"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            meta = {"operacion": "FRONTUR", "serie": "FREG351", "tabla": 10823, "fuente": "INE"}
            return [
                ContextoRecord(
                    fuente=self.fuente,
                    indicador="turistas_internacionales",
                    periodo=p.periodo,
                    valor=p.valor,
                    unidad="turistas",
                    ambito="andalucia",
                    metadatos=_meta(meta, p),
                )
                for p in oficiales.serie_ine("FREG351", 10823, anios * 12)
            ]
        return [
            ContextoRecord(
                fuente=self.fuente,
                indicador="turistas_internacionales",
                periodo=periodo,
                valor=valor,
                unidad="turistas",
                ambito="andalucia",
                metadatos={"sintetico": True, "operacion": "FRONTUR"},
            )
            for periodo, valor in _serie_mensual_sintetica(950_000, anios)
        ]


class INEEgaturConnector(FuentePublicaConnector):
    """Gasto turístico (Egatur) — INE, trimestral, ámbito Andalucía."""

    fuente = "ine_egatur"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            # El INE publica el gasto mensual en millones de euros: se agrega por
            # trimestres completos, como la serie que usa el panel.
            meta = {"operacion": "EGATUR", "serie": "FREG537", "tabla": 10839, "fuente": "INE"}
            meses = oficiales.serie_ine("FREG537", 10839, anios * 12 + 2, escala=1_000_000)
            return [
                ContextoRecord(
                    fuente=self.fuente,
                    indicador="gasto_turistico_total_eur",
                    periodo=q,
                    valor=valor,
                    unidad="euros",
                    ambito="andalucia",
                    metadatos=_meta(meta, provisional=True) if prov else dict(meta),
                )
                for q, valor, prov in oficiales.trimestres(meses)
            ]
        # Agrega la serie mensual sintética en trimestres
        mensual = _serie_mensual_sintetica(1_150_000_000, anios)  # euros/mes
        por_trimestre: dict[str, float] = {}
        for periodo, valor in mensual:
            anio, mes = periodo.split("-")
            q = (int(mes) - 1) // 3 + 1
            por_trimestre[f"{anio}-Q{q}"] = por_trimestre.get(f"{anio}-Q{q}", 0.0) + valor
        return [
            ContextoRecord(
                fuente=self.fuente,
                indicador="gasto_turistico_total_eur",
                periodo=periodo,
                valor=round(valor, 2),
                unidad="euros",
                ambito="andalucia",
                metadatos={"sintetico": True, "operacion": "EGATUR"},
            )
            for periodo, valor in sorted(por_trimestre.items())
        ]


class INEEohConnector(FuentePublicaConnector):
    """Encuesta de Ocupación Hotelera (EOH) — INE, mensual, provincia de Almería.

    Las pernoctaciones son la referencia para calibrar el factor de expansión.
    """

    fuente = "ine_eoh"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            meta = {"operacion": "EOH", "serie": "EOT1460", "tabla": 2074, "fuente": "INE"}
            return [
                ContextoRecord(
                    fuente=self.fuente,
                    indicador="pernoctaciones",
                    periodo=p.periodo,
                    valor=p.valor,
                    unidad="pernoctaciones",
                    ambito="provincia_almeria",
                    metadatos=_meta(meta, p),
                )
                for p in oficiales.serie_ine("EOT1460", 2074, anios * 12)
            ]
        return [
            ContextoRecord(
                fuente=self.fuente,
                indicador="pernoctaciones",
                periodo=periodo,
                valor=valor,
                unidad="pernoctaciones",
                ambito="provincia_almeria",
                metadatos={"sintetico": True, "operacion": "EOH"},
            )
            for periodo, valor in _serie_mensual_sintetica(420_000, anios)
        ]


class JuntaAndaluciaConnector(FuentePublicaConnector):
    """Observatorio Turístico de Andalucía — viajeros alojados, mensual."""

    fuente = "junta_andalucia"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            # IECA (Junta): explotación de la EOH, viajeros en hoteles de la provincia.
            meta = {
                "fuente": "IECA · Encuesta de Ocupación Hotelera",
                "consulta": oficiales.IECA_EOH_PROVINCIAS,
            }
            hoy = date.today()
            desde = f"{hoy.year - anios:04d}{hoy.month:02d}"
            return [
                ContextoRecord(
                    fuente=self.fuente,
                    indicador="viajeros_alojados",
                    periodo=p.periodo,
                    valor=p.valor,
                    unidad="viajeros",
                    ambito="provincia_almeria",
                    metadatos=dict(meta),
                )
                for p in oficiales.serie_ieca_viajeros(desde, f"{hoy.year:04d}{hoy.month:02d}")
            ]
        return [
            ContextoRecord(
                fuente=self.fuente,
                indicador="viajeros_alojados",
                periodo=periodo,
                valor=valor,
                unidad="viajeros",
                ambito="provincia_almeria",
                metadatos={"sintetico": True, "fuente": "Observatorio Turístico Andalucía"},
            )
            for periodo, valor in _serie_mensual_sintetica(155_000, anios)
        ]


class AENAConnector(FuentePublicaConnector):
    """Pasajeros del Aeropuerto de Almería — AENA, mensual."""

    fuente = "aena"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            meta = {"iata": "LEI", "fuente": "AENA · estadísticas de tráfico (Excel mensual)"}
            return [
                ContextoRecord(
                    fuente=self.fuente,
                    indicador="pasajeros_aeropuerto_almeria",
                    periodo=p.periodo,
                    valor=p.valor,
                    unidad="pasajeros",
                    ambito="almeria",
                    metadatos=_meta(meta, p),
                )
                for p in oficiales.serie_aena("ALMERÍA", _anios_naturales(anios))
            ]
        return [
            ContextoRecord(
                fuente=self.fuente,
                indicador="pasajeros_aeropuerto_almeria",
                periodo=periodo,
                valor=valor,
                unidad="pasajeros",
                ambito="almeria",
                metadatos={"sintetico": True, "iata": "LEI"},
            )
            for periodo, valor in _serie_mensual_sintetica(90_000, anios)
        ]


def todos_los_conectores(dry_run: bool = True) -> list[FuentePublicaConnector]:
    """Instancia los cinco conectores de fuentes públicas."""
    return [
        INEFronturConnector(dry_run=dry_run),
        INEEgaturConnector(dry_run=dry_run),
        INEEohConnector(dry_run=dry_run),
        JuntaAndaluciaConnector(dry_run=dry_run),
        AENAConnector(dry_run=dry_run),
    ]
