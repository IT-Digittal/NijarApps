"""Tests del conector Open-Meteo (parseo puro y mapeos, sin red)."""

from __future__ import annotations

from datetime import date

from nijar_dti.connectors.openmeteo import cardinal, descripcion_wmo, parsear_meteo
from nijar_dti.schemas.gemelo import MeteoActualOut


def _raw() -> dict:
    return {
        "latitude": 36.9660,
        "longitude": -2.2076,
        "current": {
            "time": "2026-08-19T07:15",
            "temperature_2m": 25.1,
            "relative_humidity_2m": 68,
            "apparent_temperature": 27.6,
            "is_day": 0,
            "precipitation": 0.0,
            "weather_code": 0,
            "wind_speed_10m": 5.8,
            "wind_direction_10m": 248,
        },
        "daily": {
            "time": ["2026-08-19", "2026-08-20"],
            "weather_code": [3, 95],
            "temperature_2m_max": [33.4, 31.0],
            "temperature_2m_min": [24.6, 23.1],
            "precipitation_probability_max": [0, 40],
        },
    }


def test_descripcion_wmo():
    assert descripcion_wmo(0) == "Despejado"
    assert descripcion_wmo(95) == "Tormenta"
    assert descripcion_wmo(None) == "Desconocido"
    assert descripcion_wmo(1234) == "Desconocido"


def test_cardinal():
    assert cardinal(0) == "N"
    assert cardinal(90) == "E"
    assert cardinal(180) == "S"
    assert cardinal(270) == "O"
    assert cardinal(248) == "OSO"
    assert cardinal(None) is None


def test_parseo_actual():
    m = parsear_meteo(_raw(), 36.966, -2.2076)
    assert m["fuente"] == "open-meteo"
    assert m["temperatura_c"] == 25.1
    assert m["sensacion_c"] == 27.6
    assert m["humedad_pct"] == 68
    assert m["descripcion"] == "Despejado"
    assert m["viento_cardinal"] == "OSO"
    assert m["es_de_dia"] is False
    assert m["medido_en"].hour == 7


def test_parseo_prevision():
    m = parsear_meteo(_raw(), 36.966, -2.2076)
    assert len(m["prevision"]) == 2
    d0 = m["prevision"][0]
    assert d0["descripcion"] == "Nublado"  # code 3
    assert d0["temp_max_c"] == 33.4 and d0["temp_min_c"] == 24.6
    assert m["prevision"][1]["descripcion"] == "Tormenta"  # code 95
    assert m["prevision"][1]["prob_precipitacion_pct"] == 40


def test_schema_valida():
    m = MeteoActualOut(**parsear_meteo(_raw(), 36.966, -2.2076))
    assert m.temperatura_c == 25.1
    assert m.prevision[0].fecha == date(2026, 8, 19)
    assert isinstance(m.prevision[1].codigo_wmo, int)


def test_current_vacio_no_rompe():
    m = parsear_meteo({"latitude": 1.0, "longitude": 2.0}, 1.0, 2.0)
    assert m["temperatura_c"] is None
    assert m["descripcion"] == "Desconocido"
    assert m["prevision"] == []
    MeteoActualOut(**m)  # sigue validando
