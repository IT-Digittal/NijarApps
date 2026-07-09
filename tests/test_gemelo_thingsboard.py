"""Tests del conector ThingsBoard del gemelo digital (parseo puro, sin red)."""

from __future__ import annotations

from nijar_dti.config import Settings
from nijar_dti.connectors.thingsboard import parsear_aforo_parque, parsear_bandera
from nijar_dti.services.gemelo_service import thingsboard_configurado

DISPOSITIVO = {"id": {"id": "abc"}, "name": "Playa de Mónsul", "type": "Bandera playas"}


def _atributos(estado: str = "Verde", lat: float | None = 36.73, lon: float | None = -2.14):
    attrs = [
        {"key": "Componente", "value": "Playa"},
        {"key": "Estado bandera", "value": estado},
    ]
    if lat is not None:
        attrs.append({"key": "Latitud", "value": lat})
    if lon is not None:
        attrs.append({"key": "Longitud", "value": lon})
    return attrs


def test_parsear_bandera_normaliza_estado():
    b = parsear_bandera(DISPOSITIVO, _atributos("Verde"))
    assert b == {
        "nombre": "Playa de Mónsul",
        "estado": "verde",
        "latitud": 36.73,
        "longitud": -2.14,
    }
    assert parsear_bandera(DISPOSITIVO, _atributos("Sin bandera"))["estado"] == "sin_bandera"
    assert parsear_bandera(DISPOSITIVO, _atributos("ROJA"))["estado"] == "roja"
    assert parsear_bandera(DISPOSITIVO, _atributos("Amarillo"))["estado"] == "amarilla"
    assert parsear_bandera(DISPOSITIVO, _atributos("???"))["estado"] == "desconocido"


def test_parsear_bandera_sin_coordenadas_devuelve_none():
    assert parsear_bandera(DISPOSITIVO, _atributos(lat=None)) is None
    assert parsear_bandera(DISPOSITIVO, _atributos(lon=None)) is None
    assert parsear_bandera(DISPOSITIVO, []) is None


def test_parsear_aforo_parque():
    telemetria = {
        "aforo_parque": [{"ts": 1783619788453, "value": "86"}],
        "entradas_parque": [{"ts": 1783619788489, "value": "1380"}],
        "salidas_parque": [{"ts": 1783619788563, "value": "1294"}],
        "total_parque": [{"ts": 1783619788662, "value": "2674"}],
        "total_motorizados": [{"ts": 1783619788763, "value": "2485"}],
        "total_no_motorizados": [{"ts": 1783619788863, "value": "80"}],
        "total_personas": [{"ts": 1783619788967, "value": "45"}],
    }
    v = parsear_aforo_parque(telemetria)
    assert v["aforo_parque"] == 86
    assert v["entradas_parque"] == 1380
    assert v["total_personas"] == 45
    assert v["ts_ms"] == 1783619788967  # el ts más reciente de todas las series


def test_parsear_aforo_parque_series_vacias():
    v = parsear_aforo_parque({})
    assert v["aforo_parque"] is None
    assert v["ts_ms"] is None
    v2 = parsear_aforo_parque({"aforo_parque": [{"ts": 1, "value": "no-numérico"}]})
    assert v2["aforo_parque"] is None


def test_thingsboard_configurado_segun_settings():
    assert not thingsboard_configurado(Settings())  # sin variables → apagado
    completo = Settings(
        thingsboard_base_url="https://plataforma.example",
        thingsboard_usuario="u@example.es",
        thingsboard_password="secreto",
    )
    assert thingsboard_configurado(completo)
    parcial = Settings(thingsboard_base_url="https://plataforma.example")
    assert not thingsboard_configurado(parcial)
