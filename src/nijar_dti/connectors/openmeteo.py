"""Cliente de solo lectura de Open-Meteo (meteorología pública, sin clave).

Open-Meteo (https://open-meteo.com) ofrece predicción y condiciones actuales
sin autenticación. Es la fuente meteorológica pública que ya combinaba la app de
Turismo del Ayuntamiento; aquí la exponemos normalizada para el tótem y el panel
(las estaciones Bettair se integran aparte, en el gemelo digital).

El parseo es una función pura (``parsear_meteo``) para poder testarlo sin red;
el cliente solo hace la petición HTTP.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

# Códigos WMO (weather_code) → descripción en español.
WMO: dict[int, str] = {
    0: "Despejado",
    1: "Principalmente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna intensa",
    56: "Llovizna helada ligera",
    57: "Llovizna helada intensa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia intensa",
    66: "Lluvia helada ligera",
    67: "Lluvia helada intensa",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada intensa",
    77: "Granos de nieve",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve intensos",
    95: "Tormenta",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo fuerte",
}

_CARDINALES = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSO",
    "SO",
    "OSO",
    "O",
    "ONO",
    "NO",
    "NNO",
]


class OpenMeteoError(RuntimeError):
    """Error de comunicación con el API de Open-Meteo."""


def descripcion_wmo(codigo: int | None) -> str:
    if codigo is None:
        return "Desconocido"
    return WMO.get(int(codigo), "Desconocido")


def cardinal(grados: float | None) -> str | None:
    if grados is None:
        return None
    return _CARDINALES[round(float(grados) / 22.5) % 16]


def _dt(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def parsear_meteo(raw: dict[str, Any], lat: float, lon: float) -> dict[str, Any]:
    """Normaliza la respuesta de Open-Meteo al esquema de la plataforma."""
    cur = raw.get("current") or {}
    codigo = cur.get("weather_code")
    is_day = cur.get("is_day")

    prevision: list[dict[str, Any]] = []
    daily = raw.get("daily") or {}
    fechas = daily.get("time") or []

    def _g(clave: str, idx: int) -> Any:
        serie = daily.get(clave) or []
        return serie[idx] if idx < len(serie) else None

    for i, fecha in enumerate(fechas):
        cod_dia = _g("weather_code", i)
        prevision.append(
            {
                "fecha": fecha,
                "codigo_wmo": cod_dia,
                "descripcion": descripcion_wmo(cod_dia),
                "temp_max_c": _g("temperature_2m_max", i),
                "temp_min_c": _g("temperature_2m_min", i),
                "prob_precipitacion_pct": _g("precipitation_probability_max", i),
            }
        )

    return {
        "fuente": "open-meteo",
        "obtenido_en": datetime.now(UTC),
        "latitud": float(raw.get("latitude", lat)),
        "longitud": float(raw.get("longitude", lon)),
        "temperatura_c": cur.get("temperature_2m"),
        "sensacion_c": cur.get("apparent_temperature"),
        "humedad_pct": cur.get("relative_humidity_2m"),
        "precipitacion_mm": cur.get("precipitation"),
        "viento_kmh": cur.get("wind_speed_10m"),
        "viento_dir_grados": cur.get("wind_direction_10m"),
        "viento_cardinal": cardinal(cur.get("wind_direction_10m")),
        "codigo_wmo": codigo,
        "descripcion": descripcion_wmo(codigo),
        "es_de_dia": (bool(is_day) if is_day is not None else None),
        "medido_en": _dt(cur.get("time")),
        "prevision": prevision,
    }


class ClienteOpenMeteo:
    """Cliente REST mínimo de Open-Meteo (solo lectura, sin credenciales)."""

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1",
        timeout_seconds: int = 12,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def actual(
        self, latitud: float, longitud: float, dias_prevision: int = 3
    ) -> dict[str, Any]:
        params = {
            "latitude": latitud,
            "longitude": longitud,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,"
                "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            ),
            "timezone": "auto",
            "forecast_days": max(1, min(dias_prevision, 7)),
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(f"{self._base}/forecast", params=params)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                detalle = str(exc) or type(exc).__name__
                raise OpenMeteoError(f"Error al consultar Open-Meteo: {detalle}") from exc
        try:
            raw = resp.json()
        except ValueError as exc:
            raise OpenMeteoError("Open-Meteo no devolvió JSON válido") from exc
        return parsear_meteo(raw, latitud, longitud)
