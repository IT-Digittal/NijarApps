"""Tests del conector Bettair del gemelo digital (parseo puro, sin red).

El fixture reproduce la respuesta real de ``GET /orion/v2/entities`` de la API
v3 de Bettair (una entidad ``info`` y una ``data`` por estación).
"""

from __future__ import annotations

from nijar_dti.config import Settings
from nijar_dti.connectors.bettair import parsear_estaciones, resumen_estaciones
from nijar_dti.services.gemelo_service import bettair_configurado


def _entidad_info(sid: str, lat: float | None = 36.84688, lon: float | None = -2.040669):
    pos = {"lat": lat, "long": lon} if lat is not None else {}
    return {
        "id": sid,
        "type": "info",
        "airQualityIndexes": {
            "type": "StructuredValue",
            "value": {"EAQI": {"pollutant": "O3", "value": 1}, "AQI": {"value": 24}},
        },
        "battery": {"type": "Number", "value": 100},
        "lastConnection": {"type": "Text", "value": "2026-07-10T09:40:20.938Z"},
        "position": {"type": "StructuredValue", "value": pos},
        "state": {"type": "Text", "value": "active"},
    }


def _entidad_data(sid: str):
    valores = {
        "NO2": 10.4,
        "O3": 66.7,
        "PM1": 6,
        "PM10": 33,
        "PM2P5": 7,
        "pressure": 1002.9,
        "relativeHumidity": 26.2,
        "temperature": 36.63,
    }
    ent: dict = {"id": sid, "type": "data"}
    for k, v in valores.items():
        ent[k] = {"type": "Number", "value": v}
    ent["timestamp"] = {"type": "Text", "value": "2026-07-10T09:30:00.000Z"}
    return ent


def test_parsear_estaciones_combina_info_y_data():
    filas = parsear_estaciones([_entidad_info("BET00260097"), _entidad_data("BET00260097")])
    assert len(filas) == 1
    e = filas[0]
    assert e["id"] == "BET00260097"
    assert e["latitud"] == 36.84688 and e["longitud"] == -2.040669
    assert e["estado"] == "active"
    assert e["eaqi"] == 1 and e["eaqi_texto"] == "buena"
    assert e["temperatura_c"] == 36.63
    assert e["no2_ugm3"] == 10.4 and e["pm10_ugm3"] == 33
    assert e["medido_en"] == "2026-07-10T09:30:00.000Z"


def test_parsear_estaciones_sin_posicion_se_descarta():
    assert parsear_estaciones([_entidad_info("X", lat=None), _entidad_data("X")]) == []


def test_parsear_estaciones_sin_data_devuelve_medidas_nulas():
    filas = parsear_estaciones([_entidad_info("BET1")])
    assert len(filas) == 1
    assert filas[0]["temperatura_c"] is None
    assert filas[0]["eaqi"] == 1  # el índice viene de la entidad info


def test_parsear_estaciones_eaqi_desconocido():
    ent = _entidad_info("BET2")
    ent["airQualityIndexes"]["value"] = {}
    filas = parsear_estaciones([ent])
    assert filas[0]["eaqi"] is None and filas[0]["eaqi_texto"] is None


def _estacion(sid, temperatura, eaqi, estado="active", medido="2026-07-10T09:35:00Z"):
    return {
        "id": sid,
        "estado": estado,
        "temperatura_c": temperatura,
        "humedad_pct": 30.0,
        "eaqi": eaqi,
        "medido_en": medido,
    }


def test_resumen_estaciones_agrega_activas():
    r = resumen_estaciones(
        [
            _estacion("A", 36.6, 1),
            _estacion("B", 32.8, 2, medido="2026-07-10T09:40:00Z"),
            _estacion("C", 99.0, 6, estado="inactive"),  # inactiva: no cuenta
        ]
    )
    assert r["estaciones_activas"] == 2
    assert r["temperatura_media_c"] == 34.7
    assert r["temperatura_max_c"] == 36.6
    assert r["eaqi_peor"] == 2 and r["eaqi_peor_texto"] == "razonable"
    assert r["medido_en"] == "2026-07-10T09:40:00Z"


def test_resumen_estaciones_vacio():
    r = resumen_estaciones([])
    assert r["estaciones_activas"] == 0
    assert r["temperatura_media_c"] is None
    assert r["eaqi_peor"] is None and r["medido_en"] is None


def test_bettair_configurado_segun_settings():
    assert not bettair_configurado(Settings())
    completo = Settings(bettair_client_id="org@abc", bettair_client_secret="secreto")
    assert bettair_configurado(completo)
    parcial = Settings(bettair_client_id="org@abc")
    assert not bettair_configurado(parcial)
