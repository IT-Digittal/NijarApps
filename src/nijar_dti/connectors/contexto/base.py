"""Clase base de los conectores de fuentes públicas (contexto histórico).

Cada conector concreto (INE Frontur/Egatur/EOH, Junta, AENA) hereda de
``FuentePublicaConnector`` e implementa ``fetch_series``. La clase base
define el registro normalizado ``ContextoRecord`` y el modo ``dry_run``.

En ``dry_run`` (por defecto en desarrollo y en este entorno sin red) los
conectores devuelven series sintéticas coherentes con la estacionalidad
real de Almería/Cabo de Gata, suficientes para validar el pipeline, el
modelo semántico y el cálculo del factor de expansión sin llamar a las
APIs externas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ContextoConnectorError(Exception):
    """Error genérico de un conector de contexto."""


@dataclass(frozen=True)
class ContextoRecord:
    """Observación normalizada de una serie histórica oficial."""

    fuente: str  # ver FuenteContexto
    indicador: str
    periodo: str  # "AAAA-MM" | "AAAA-Qn" | "AAAA"
    valor: float
    unidad: str | None = None
    ambito: str = "provincia_almeria"
    metadatos: dict[str, Any] = field(default_factory=dict)

    def clave(self) -> tuple[str, str, str, str]:
        """Clave de idempotencia (fuente, indicador, periodo, ámbito)."""
        return (self.fuente, self.indicador, self.periodo, self.ambito)


class FuentePublicaConnector(ABC):
    """Interfaz común para los conectores de fuentes públicas."""

    fuente: str  # la subclase debe definirlo

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    @abstractmethod
    def fetch_series(self, anios: int = 3) -> list[ContextoRecord]:
        """Devuelve las series de los últimos ``anios`` años.

        En modo ``dry_run`` devuelve datos sintéticos; en modo real consulta
        la API/feed oficial de la fuente.
        """

    @property
    def is_configured(self) -> bool:
        """Las fuentes públicas no requieren credenciales (acceso libre)."""
        return True
