"""Conectores concretos de fuentes públicas oficiales.

Implementan el patrón del proyecto: ruta real con ``httpx`` cuando
``dry_run`` es False y datos sintéticos coherentes cuando es True (modo por
defecto). Las series sintéticas reproducen la fuerte estacionalidad estival
de Almería/Cabo de Gata para que el pipeline, el modelo semántico y el
cálculo del factor de expansión sean validables sin red.

Las APIs reales son de acceso libre y sin credenciales:
- INE: API Tempus3 JSON (https://servicios.ine.es/wstempus/js/ES/...).
- Junta de Andalucía: portal de datos abiertos.
- AENA: estadísticas de tráfico de pasajeros.
"""

from __future__ import annotations

from datetime import date

from nijar_dti.connectors.contexto.base import (
    ContextoConnectorError,
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


class _DryRunMixin(FuentePublicaConnector):
    """Si no es dry_run y no hay implementación real, falla de forma explícita."""

    def _real_no_disponible(self) -> list[ContextoRecord]:
        raise ContextoConnectorError(
            f"Conector '{self.fuente}' en modo real no configurado en este entorno. "
            "Use dry_run=True o implemente la llamada a la API oficial."
        )


class INEFronturConnector(_DryRunMixin):
    """Turismo internacional (Frontur) — INE, mensual, ámbito Andalucía."""

    fuente = "ine_frontur"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            return self._real_no_disponible()
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


class INEEgaturConnector(_DryRunMixin):
    """Gasto turístico (Egatur) — INE, trimestral, ámbito Andalucía."""

    fuente = "ine_egatur"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            return self._real_no_disponible()
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


class INEEohConnector(_DryRunMixin):
    """Encuesta de Ocupación Hotelera (EOH) — INE, mensual, provincia de Almería.

    Las pernoctaciones son la referencia para calibrar el factor de expansión.
    """

    fuente = "ine_eoh"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            return self._real_no_disponible()
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


class JuntaAndaluciaConnector(_DryRunMixin):
    """Observatorio Turístico de Andalucía — viajeros alojados, mensual."""

    fuente = "junta_andalucia"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            return self._real_no_disponible()
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


class AENAConnector(_DryRunMixin):
    """Pasajeros del Aeropuerto de Almería — AENA, mensual."""

    fuente = "aena"

    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        if not self.dry_run:
            return self._real_no_disponible()
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
