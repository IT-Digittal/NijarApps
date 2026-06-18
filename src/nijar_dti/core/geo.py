"""Utilidades geográficas para el planificador de rutas (A.1 / B.2).

Funciones puras (sin dependencias externas ni BBDD) para calcular distancias
geodésicas y ordenar un itinerario de paradas. El planificador de rutas del
tótem y del chatbot las usa para proponer visitas encadenadas a los recursos
turísticos del destino (ruta ciclista Rodalquilar–Albaricoques, playas, etc.).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

RADIO_TIERRA_M = 6_371_000.0

# Velocidades medias por modo de desplazamiento (km/h) para estimar duración.
VELOCIDADES_KMH = {
    "a_pie": 4.5,
    "bici": 15.0,
    "coche": 50.0,
}


@dataclass(frozen=True)
class Parada:
    """Punto candidato de un itinerario."""

    id: str
    nombre: str
    categoria: str
    lat: float
    lon: float


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia geodésica en metros entre dos puntos (fórmula de Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * RADIO_TIERRA_M * math.asin(math.sqrt(a))


def ordenar_itinerario(
    inicio_lat: float,
    inicio_lon: float,
    paradas: list[Parada],
    max_paradas: int | None = None,
) -> list[Parada]:
    """Ordena las paradas con vecino más cercano (greedy) desde el origen.

    Heurística simple, determinista y explicable: en cada paso se elige la
    parada no visitada más próxima. Suficiente para itinerarios turísticos de
    pocas decenas de puntos; un TSP exacto sería innecesario y costoso.
    """
    restantes = list(paradas)
    ruta: list[Parada] = []
    lat, lon = inicio_lat, inicio_lon
    tope = max_paradas if max_paradas is not None else len(restantes)

    while restantes and len(ruta) < tope:
        siguiente = min(restantes, key=lambda p: haversine_m(lat, lon, p.lat, p.lon))
        ruta.append(siguiente)
        restantes.remove(siguiente)
        lat, lon = siguiente.lat, siguiente.lon
    return ruta


def distancia_total_m(
    inicio_lat: float, inicio_lon: float, ruta: list[Parada]
) -> float:
    """Distancia total recorrida (origen → parada 1 → … → parada n) en metros."""
    total = 0.0
    lat, lon = inicio_lat, inicio_lon
    for p in ruta:
        total += haversine_m(lat, lon, p.lat, p.lon)
        lat, lon = p.lat, p.lon
    return round(total, 1)


def duracion_estimada_min(distancia_m: float, modo: str = "bici") -> int:
    """Duración estimada de desplazamiento en minutos para una distancia dada."""
    velocidad = VELOCIDADES_KMH.get(modo, VELOCIDADES_KMH["bici"])
    horas = (distancia_m / 1000.0) / velocidad
    return int(round(horas * 60))
