"""Lógica pura de Acuerdos de Nivel de Servicio (ANS) y disponibilidad (C.1).

Centraliza la matriz ANS del contrato y el cálculo del cumplimiento por
incidencia y de la disponibilidad por componente a partir del tiempo de
indisponibilidad real registrado en las incidencias. Funciones puras,
testeables sin BBDD.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Matriz ANS (Memoria Técnica): objetivos de respuesta y resolución por
# severidad, en horas.
SLA_ANS: dict[str, dict[str, float]] = {
    "critica": {"respuesta_h": 1, "resolucion_h": 8},
    "alta": {"respuesta_h": 4, "resolucion_h": 12},
    "media": {"respuesta_h": 8, "resolucion_h": 48},
    "baja": {"respuesta_h": 12, "resolucion_h": 120},
}

# SLA de disponibilidad mensual contractual (PPT C.1): 99 %.
SLA_DISPONIBILIDAD_PORC = 99.0


def horas_entre(inicio: datetime | None, fin: datetime | None) -> float | None:
    """Horas transcurridas entre dos instantes; None si falta alguno."""
    if inicio is None or fin is None:
        return None
    return round((fin - inicio).total_seconds() / 3600, 2)


@dataclass
class EvaluacionANS:
    """Cumplimiento ANS de una incidencia concreta."""

    respuesta_h: float | None
    resolucion_h: float | None
    cumple_respuesta: bool | None
    cumple_resolucion: bool | None

    @property
    def cumple(self) -> bool | None:
        if self.cumple_respuesta is None and self.cumple_resolucion is None:
            return None
        return bool(self.cumple_respuesta) and bool(self.cumple_resolucion)


def evalua_ans(
    severidad: str,
    detectada_en: datetime,
    respondida_en: datetime | None,
    resuelta_en: datetime | None,
) -> EvaluacionANS:
    """Evalúa el cumplimiento de los objetivos ANS de una incidencia."""
    objetivos = SLA_ANS.get(severidad, SLA_ANS["media"])
    respuesta_h = horas_entre(detectada_en, respondida_en)
    resolucion_h = horas_entre(detectada_en, resuelta_en)
    cumple_respuesta = respuesta_h <= objetivos["respuesta_h"] if respuesta_h is not None else None
    cumple_resolucion = (
        resolucion_h <= objetivos["resolucion_h"] if resolucion_h is not None else None
    )
    return EvaluacionANS(respuesta_h, resolucion_h, cumple_respuesta, cumple_resolucion)


def disponibilidad_porcentaje(downtime_minutos: float, periodo_minutos: float) -> float:
    """Disponibilidad (%) = (1 − downtime/periodo)·100, acotada a [0, 100]."""
    if periodo_minutos <= 0:
        return 100.0
    pct = (1 - max(downtime_minutos, 0.0) / periodo_minutos) * 100
    return round(min(max(pct, 0.0), 100.0), 3)
