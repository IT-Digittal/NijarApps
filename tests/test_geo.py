"""Tests de las utilidades geográficas del planificador de rutas."""

from __future__ import annotations

from nijar_dti.core.geo import (
    Parada,
    distancia_total_m,
    duracion_estimada_min,
    haversine_m,
    ordenar_itinerario,
)

# Coordenadas reales aproximadas del entorno de Níjar / Cabo de Gata
RODALQUILAR = (36.8470, -2.0410)
ALBARICOQUES = (36.9330, -2.1230)
MONSUL = (36.7290, -2.1490)


def test_haversine_cero():
    assert haversine_m(*RODALQUILAR, *RODALQUILAR) == 0.0


def test_haversine_distancia_conocida():
    # Rodalquilar–Albaricoques ~ 12-13 km en línea recta
    d = haversine_m(*RODALQUILAR, *ALBARICOQUES)
    assert 9_000 < d < 16_000


def test_haversine_simetrica():
    a = haversine_m(*RODALQUILAR, *MONSUL)
    b = haversine_m(*MONSUL, *RODALQUILAR)
    assert abs(a - b) < 0.01


def _paradas():
    return [
        Parada("1", "Albaricoques", "ruta", *ALBARICOQUES),
        Parada("2", "Mónsul", "playa", *MONSUL),
    ]


def test_ordenar_itinerario_vecino_mas_cercano():
    # Desde Rodalquilar, Albaricoques está más cerca que Mónsul -> se visita antes
    d_alb = haversine_m(*RODALQUILAR, *ALBARICOQUES)
    d_mon = haversine_m(*RODALQUILAR, *MONSUL)
    assert d_alb < d_mon
    ruta = ordenar_itinerario(*RODALQUILAR, _paradas())
    assert [p.id for p in ruta] == ["1", "2"]


def test_ordenar_itinerario_respeta_max_paradas():
    ruta = ordenar_itinerario(*RODALQUILAR, _paradas(), max_paradas=1)
    assert len(ruta) == 1


def test_ordenar_itinerario_vacio():
    assert ordenar_itinerario(*RODALQUILAR, []) == []


def test_distancia_total_acumula():
    ruta = ordenar_itinerario(*RODALQUILAR, _paradas())
    total = distancia_total_m(*RODALQUILAR, ruta)
    # debe ser >= que ir directo a la primera parada
    directo = haversine_m(*RODALQUILAR, ruta[0].lat, ruta[0].lon)
    assert total >= directo


def test_duracion_estimada_por_modo():
    # 15 km: a pie tarda más que en bici, y en bici más que en coche
    a_pie = duracion_estimada_min(15_000, "a_pie")
    bici = duracion_estimada_min(15_000, "bici")
    coche = duracion_estimada_min(15_000, "coche")
    assert a_pie > bici > coche
    assert bici == 60  # 15 km / 15 km/h = 1 h
