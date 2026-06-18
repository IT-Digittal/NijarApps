"""Utilidades de anonimización y privacidad (RGPD / DNSH).

Centraliza la regla de **k-anonimato** que protege los agregados que se
exponen en los dashboards del observatorio Big Data: ninguna celda que
agrupe a menos de ``K_ANONIMATO_MIN`` individuos puede mostrarse, para
evitar la reidentificación de visitantes a partir de combinaciones poco
frecuentes (p. ej. un único turista de un idioma minoritario en una franja
horaria concreta).

La regla se aplica de forma transversal a cualquier KPI agregado derivado
de señales de movilidad o de comportamiento individual (composición
lingüística de visitantes, flujos entre POIs, etc.). Documentado en
``docs/big-data/metodologia-y-limitaciones.md``.
"""

from __future__ import annotations

from collections.abc import Mapping

# Umbral mínimo de individuos por celda para poder publicar un agregado.
# Valor conservador alineado con la práctica habitual de movilidad turística
# (Eurostat, estudios de telefonía móvil) y con la DPIA de la plataforma.
K_ANONIMATO_MIN = 5


def cumple_k_anonimato(n: int, k: int = K_ANONIMATO_MIN) -> bool:
    """Indica si un conteo ``n`` puede publicarse bajo la regla de k-anonimato."""
    return n >= k


def suprimir_k_anonimato(
    conteos: Mapping[str, int], k: int = K_ANONIMATO_MIN
) -> tuple[dict[str, int], int]:
    """Aplica k-anonimato a un diccionario ``clave -> conteo``.

    Devuelve la tupla ``(conteos_publicables, total_suprimido)`` donde
    ``conteos_publicables`` solo contiene las celdas con ``n >= k`` y
    ``total_suprimido`` es la suma de los individuos ocultados (que sí cuentan
    para el total pero no se desglosan, preservando la coherencia del 100 %).

    No se devuelve nunca una celda residual con la cuenta suprimida, porque
    revelar "otros = 3" volvería a romper el k-anonimato.
    """
    publicables: dict[str, int] = {}
    suprimido = 0
    for clave, n in conteos.items():
        if cumple_k_anonimato(n, k):
            publicables[clave] = n
        else:
            suprimido += max(n, 0)
    return publicables, suprimido
