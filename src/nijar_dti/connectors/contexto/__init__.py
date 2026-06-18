"""Conectores de backfill a fuentes públicas oficiales (contexto histórico).

Aportan al observatorio el histórico largo del que carece un sistema que
arranca en el mes 1, y permiten calibrar el factor de expansión de las
señales muestrales contra las pernoctaciones oficiales (INE EOH).

Fuentes: INE (Frontur, Egatur, EOH), Junta de Andalucía y AENA.
Todas de acceso libre / datos abiertos — sin datos personales.
"""

from nijar_dti.connectors.contexto.base import ContextoRecord, FuentePublicaConnector
from nijar_dti.connectors.contexto.expansion import calcular_factor_expansion
from nijar_dti.connectors.contexto.fuentes import (
    AENAConnector,
    INEEgaturConnector,
    INEEohConnector,
    INEFronturConnector,
    JuntaAndaluciaConnector,
    todos_los_conectores,
)

__all__ = [
    "ContextoRecord",
    "FuentePublicaConnector",
    "INEFronturConnector",
    "INEEgaturConnector",
    "INEEohConnector",
    "JuntaAndaluciaConnector",
    "AENAConnector",
    "todos_los_conectores",
    "calcular_factor_expansion",
]
