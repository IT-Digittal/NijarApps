"""Cliente de solo lectura de la plataforma ThingsBoard del DTI de Níjar.

Primera vertical externa integrada en el gemelo digital (Fase 4): la
plataforma IoT municipal existente (banderas de playa, aforo del Parque
Natural Cabo de Gata, cámaras de acceso, beacons). Autenticación JWT con
caché de token y funciones de parseo puras (testeables sin red).

Las credenciales se leen de ``THINGSBOARD_BASE_URL`` / ``THINGSBOARD_USUARIO``
/ ``THINGSBOARD_PASSWORD`` en el entorno; nunca se versionan.
"""

from __future__ import annotations

import time
from typing import Any

import httpx


class ThingsBoardError(RuntimeError):
    """Error de comunicación o autenticación con ThingsBoard."""


class ClienteThingsBoard:
    """Cliente REST mínimo (login + lecturas de entidades y telemetría)."""

    def __init__(
        self, base_url: str, usuario: str, password: str, timeout_seconds: int = 12
    ) -> None:
        self._base = base_url.rstrip("/")
        self._usuario = usuario
        self._password = password
        self._timeout = timeout_seconds
        self._token: str | None = None
        self._token_expira = 0.0

    async def _obtener_token(self, client: httpx.AsyncClient) -> str:
        """Token JWT con caché (ThingsBoard los emite con ~2,5 h de vida)."""
        if self._token and time.monotonic() < self._token_expira:
            return self._token
        try:
            resp = await client.post(
                f"{self._base}/api/auth/login",
                json={"username": self._usuario, "password": self._password},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ThingsBoardError(f"Login en ThingsBoard fallido: {exc}") from exc
        self._token = str(resp.json()["token"])
        self._token_expira = time.monotonic() + 20 * 60  # margen conservador
        return self._token

    async def _get(self, ruta: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            token = await self._obtener_token(client)
            try:
                resp = await client.get(
                    f"{self._base}{ruta}",
                    params=params,
                    headers={"X-Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 401:  # token revocado: reintentar una vez
                    self._token = None
                    token = await self._obtener_token(client)
                    resp = await client.get(
                        f"{self._base}{ruta}",
                        params=params,
                        headers={"X-Authorization": f"Bearer {token}"},
                    )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise ThingsBoardError(f"GET {ruta} fallido: {exc}") from exc
            return resp.json()

    async def dispositivos(self, tipo: str, page_size: int = 200) -> list[dict[str, Any]]:
        datos = await self._get(
            "/api/tenant/devices", {"pageSize": page_size, "page": 0, "type": tipo}
        )
        return list(datos.get("data", []))

    async def activos(self, page_size: int = 100) -> list[dict[str, Any]]:
        datos = await self._get("/api/tenant/assets", {"pageSize": page_size, "page": 0})
        return list(datos.get("data", []))

    async def atributos(self, tipo_entidad: str, id_entidad: str) -> list[dict[str, Any]]:
        return list(
            await self._get(f"/api/plugins/telemetry/{tipo_entidad}/{id_entidad}/values/attributes")
        )

    async def telemetria_actual(
        self, tipo_entidad: str, id_entidad: str, claves: list[str]
    ) -> dict[str, Any]:
        return dict(
            await self._get(
                f"/api/plugins/telemetry/{tipo_entidad}/{id_entidad}/values/timeseries",
                {"keys": ",".join(claves)},
            )
        )


# --------------------------- Parseo puro (sin red) ---------------------------

ESTADOS_BANDERA = {
    "verde": "verde",
    "amarilla": "amarilla",
    "amarillo": "amarilla",
    "roja": "roja",
    "rojo": "roja",
    "sin bandera": "sin_bandera",
}

CLAVES_AFORO_PARQUE = [
    "aforo_parque",
    "entradas_parque",
    "salidas_parque",
    "total_parque",
    "total_motorizados",
    "total_no_motorizados",
    "total_personas",
]


def parsear_bandera(
    dispositivo: dict[str, Any], atributos: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Combina el dispositivo «Bandera playas» con sus atributos de servidor.

    Devuelve ``None`` si faltan las coordenadas (no se puede pintar en el mapa).
    """
    attrs = {a.get("key"): a.get("value") for a in atributos}
    lat, lon = attrs.get("Latitud"), attrs.get("Longitud")
    if not isinstance(lat, int | float) or not isinstance(lon, int | float):
        return None
    crudo = str(attrs.get("Estado bandera", "")).strip().lower()
    return {
        "nombre": str(dispositivo.get("name", "")),
        "estado": ESTADOS_BANDERA.get(crudo, "desconocido"),
        "latitud": float(lat),
        "longitud": float(lon),
    }


def _entero(valor: Any) -> int | None:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def parsear_aforo_parque(telemetria: dict[str, Any]) -> dict[str, Any]:
    """Última muestra de cada serie del activo ``parque_cabo_de_gata``.

    ThingsBoard devuelve ``{clave: [{"ts": ms, "value": "86"}, ...]}``; se toma
    el punto más reciente y el ``ts`` máximo como marca de actualización.
    El contador municipal de entradas/salidas puede desfasarse y arrojar
    valores negativos sin sentido físico; se acotan a 0.
    """
    valores: dict[str, int | None] = {}
    ts_max = 0
    for clave in CLAVES_AFORO_PARQUE:
        puntos = telemetria.get(clave) or []
        entero = _entero(puntos[0]["value"]) if puntos else None
        valores[clave] = max(0, entero) if entero is not None else None
        if puntos:
            ts_max = max(ts_max, int(puntos[0].get("ts", 0)))
    valores["ts_ms"] = ts_max or None
    return valores
