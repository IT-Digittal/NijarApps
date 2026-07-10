"""Cliente de solo lectura de la red Bettair de calidad del aire y meteorología.

Segunda vertical externa del gemelo digital (Fase 4): 5 estaciones Bettair
instaladas en el municipio (San José, Rodalquilar, Las Negras, Agua Amarga y
Campohermoso) que miden contaminantes (NO2, O3, PM), meteorología y ruido.

La API v3 (https://docs.cloud.bettair.city/api) usa OAuth 2.0 con
``client_credentials`` y expone las estaciones como entidades FIWARE/NGSI vía
Orion Context Broker — el mismo estándar de la plataforma. Credenciales en
``BETTAIR_CLIENT_ID`` / ``BETTAIR_CLIENT_SECRET``; nunca se versionan.
"""

from __future__ import annotations

import time
from typing import Any

import httpx


class BettairError(RuntimeError):
    """Error de comunicación o autenticación con la API de Bettair."""


class ClienteBettair:
    """Cliente REST mínimo (token OAuth2 con caché + entidades Orion)."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.v3.bettair.city",
        timeout_seconds: int = 12,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout = timeout_seconds
        self._token: str | None = None
        self._token_expira = 0.0

    async def _obtener_token(self, client: httpx.AsyncClient) -> str:
        """Access token con caché (Bettair los emite con 600 s de vida)."""
        if self._token and time.monotonic() < self._token_expira:
            return self._token
        try:
            resp = await client.post(
                f"{self._base}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise BettairError(f"Login OAuth2 en Bettair fallido: {exc}") from exc
        datos = resp.json()
        self._token = str(datos["access_token"])
        margen = max(int(datos.get("expires_in", 600)) - 60, 60)
        self._token_expira = time.monotonic() + margen
        return self._token

    async def _get(self, ruta: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            token = await self._obtener_token(client)
            try:
                resp = await client.get(
                    f"{self._base}{ruta}",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 401:  # token caducado: reintentar una vez
                    self._token = None
                    token = await self._obtener_token(client)
                    resp = await client.get(
                        f"{self._base}{ruta}",
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                elif resp.status_code >= 500:  # la API emite 500 transitorios
                    resp = await client.get(
                        f"{self._base}{ruta}",
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise BettairError(f"GET {ruta} fallido: {exc}") from exc
            return resp.json()

    async def entidades(self) -> list[dict[str, Any]]:
        """Entidades Orion: por estación, una ``info`` y una ``data``."""
        return list(await self._get("/orion/v2/entities"))


# --------------------------- Parseo puro (sin red) ---------------------------

# EAQI (European Air Quality Index): 1 buena … 6 extremadamente mala
NIVELES_EAQI = {
    1: "buena",
    2: "razonable",
    3: "moderada",
    4: "desfavorable",
    5: "muy desfavorable",
    6: "extremadamente desfavorable",
}


def _valor(entidad: dict[str, Any], attr: str) -> Any:
    v = entidad.get(attr)
    return v.get("value") if isinstance(v, dict) else None


def parsear_estaciones(entidades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combina las entidades ``info`` y ``data`` de cada estación Bettair.

    Devuelve una fila por estación con posición, estado, índice EAQI y las
    últimas mediciones. Las estaciones sin posición se descartan (no se pueden
    pintar en el gemelo).
    """
    info: dict[str, dict[str, Any]] = {}
    data: dict[str, dict[str, Any]] = {}
    for e in entidades:
        destino = info if e.get("type") == "info" else data if e.get("type") == "data" else None
        if destino is not None and e.get("id"):
            destino[e["id"]] = e

    estaciones = []
    for sid, ent in sorted(info.items()):
        pos = _valor(ent, "position") or {}
        lat, lon = pos.get("lat"), pos.get("long")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            continue
        indices = _valor(ent, "airQualityIndexes") or {}
        eaqi = (indices.get("EAQI") or {}).get("value")
        medidas = data.get(sid, {})
        estaciones.append(
            {
                "id": sid,
                "latitud": float(lat),
                "longitud": float(lon),
                "estado": str(_valor(ent, "state") or "desconocido"),
                "bateria_pct": _valor(ent, "battery"),
                "ultima_conexion": _valor(ent, "lastConnection"),
                "medido_en": _valor(medidas, "timestamp"),
                "eaqi": eaqi if isinstance(eaqi, int) else None,
                "eaqi_texto": NIVELES_EAQI.get(eaqi) if isinstance(eaqi, int) else None,
                "temperatura_c": _valor(medidas, "temperature"),
                "humedad_pct": _valor(medidas, "relativeHumidity"),
                "presion_hpa": _valor(medidas, "pressure"),
                "no2_ugm3": _valor(medidas, "NO2"),
                "o3_ugm3": _valor(medidas, "O3"),
                "pm25_ugm3": _valor(medidas, "PM2P5"),
                "pm10_ugm3": _valor(medidas, "PM10"),
            }
        )
    return estaciones
