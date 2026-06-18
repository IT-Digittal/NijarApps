"""Cálculo del factor de expansión de señales muestrales.

Las señales propias del observatorio que captan solo una fracción de los
visitantes (WiFi público, beacons) deben multiplicarse por un **factor de
expansión** para estimar el total. El factor se calibra contra una
referencia oficial censal/representativa (pernoctaciones INE EOH),
convirtiendo pernoctaciones en visitantes mediante la estancia media.

Procedimiento documentado en ``docs/big-data/metodologia-y-limitaciones.md``
y revisable trimestralmente (detección de deriva).
"""

from __future__ import annotations

from dataclasses import dataclass

# Factor por defecto cuando aún no hay datos propios para calibrar
# (≈ cobertura del 15 % del WiFi público → 1/0,15 ≈ 6,7).
FACTOR_EXPANSION_PRELIMINAR = 6.7
ESTANCIA_MEDIA_NOCHES = 3.5  # referencia litoral almeriense


@dataclass
class FactorExpansion:
    """Resultado de la calibración del factor de expansión."""

    factor: float
    cobertura_estimada_pct: float
    metodo: str
    muestra_referencia: int | None = None
    visitantes_oficiales_estimados: float | None = None
    es_preliminar: bool = False


def calcular_factor_expansion(
    muestra_periodo: int | None = None,
    pernoctaciones_periodo: float | None = None,
    estancia_media_noches: float = ESTANCIA_MEDIA_NOCHES,
) -> FactorExpansion:
    """Calibra el factor de expansión para un periodo.

    - Si hay ``muestra_periodo`` (p. ej. conexiones WiFi únicas) y
      ``pernoctaciones_periodo`` oficiales, calcula el factor real:
      ``visitantes_oficiales = pernoctaciones / estancia_media`` y
      ``factor = visitantes_oficiales / muestra``.
    - Si falta cualquiera de los dos, devuelve el factor preliminar (6,7)
      marcado como ``es_preliminar=True`` para que el dashboard lo señale.
    """
    if (
        muestra_periodo
        and muestra_periodo > 0
        and pernoctaciones_periodo
        and pernoctaciones_periodo > 0
        and estancia_media_noches > 0
    ):
        visitantes_oficiales = pernoctaciones_periodo / estancia_media_noches
        factor = visitantes_oficiales / muestra_periodo
        cobertura = (muestra_periodo / visitantes_oficiales) * 100 if visitantes_oficiales else 0.0
        return FactorExpansion(
            factor=round(factor, 3),
            cobertura_estimada_pct=round(cobertura, 2),
            metodo="calibrado_eoh",
            muestra_referencia=muestra_periodo,
            visitantes_oficiales_estimados=round(visitantes_oficiales, 1),
            es_preliminar=False,
        )

    return FactorExpansion(
        factor=FACTOR_EXPANSION_PRELIMINAR,
        cobertura_estimada_pct=round(100 / FACTOR_EXPANSION_PRELIMINAR, 2),
        metodo="preliminar_por_defecto",
        es_preliminar=True,
    )
