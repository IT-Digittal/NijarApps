"""Servicio del gemelo digital: lectura de verticales externas (ThingsBoard).

Agrega y cachea (TTL corto en memoria) los datos de la plataforma IoT
municipal para no repercutir cada visita del panel en la plataforma origen.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.bettair import ClienteBettair, parsear_estaciones
from nijar_dti.connectors.thingsboard import (
    CLAVES_AFORO_PARQUE,
    ClienteThingsBoard,
    parsear_aforo_parque,
    parsear_bandera,
)
from nijar_dti.schemas.gemelo import (
    AforoParqueOut,
    BanderaPlayaOut,
    BanderasPlayasOut,
    EstacionAireOut,
    EstacionesAireOut,
    EstadoGemelo,
)

_TTL_SEGUNDOS = 60
_cache: dict[str, tuple[float, Any]] = {}
_cliente: ClienteThingsBoard | None = None
_cliente_bettair: ClienteBettair | None = None

ACTIVO_AFORO_PARQUE = "parque_cabo_de_gata"
TIPO_BANDERAS = "Bandera playas"


def thingsboard_configurado(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return bool(s.thingsboard_base_url and s.thingsboard_usuario and s.thingsboard_password)


def bettair_configurado(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return bool(s.bettair_client_id and s.bettair_client_secret)


def estado_gemelo() -> EstadoGemelo:
    return EstadoGemelo(
        thingsboard_configurado=thingsboard_configurado(),
        bettair_configurado=bettair_configurado(),
    )


def _obtener_cliente() -> ClienteThingsBoard:
    global _cliente
    if _cliente is None:
        s = get_settings()
        _cliente = ClienteThingsBoard(
            s.thingsboard_base_url,
            s.thingsboard_usuario,
            s.thingsboard_password,
            s.thingsboard_timeout_seconds,
        )
    return _cliente


def _cacheado(clave: str) -> Any | None:
    entrada = _cache.get(clave)
    if entrada and time.monotonic() - entrada[0] < _TTL_SEGUNDOS:
        return entrada[1]
    return None


def _obtener_cliente_bettair() -> ClienteBettair:
    global _cliente_bettair
    if _cliente_bettair is None:
        s = get_settings()
        _cliente_bettair = ClienteBettair(
            s.bettair_client_id,
            s.bettair_client_secret,
            s.bettair_base_url,
            s.bettair_timeout_seconds,
        )
    return _cliente_bettair


async def estaciones_aire() -> EstacionesAireOut:
    if (hit := _cacheado("aire")) is not None:
        return hit  # type: ignore[no-any-return]
    entidades = await _obtener_cliente_bettair().entidades()
    estaciones = [EstacionAireOut(**e) for e in parsear_estaciones(entidades)]
    resultado = EstacionesAireOut(
        obtenido_en=datetime.now(UTC), total=len(estaciones), estaciones=estaciones
    )
    _cache["aire"] = (time.monotonic(), resultado)
    return resultado


async def banderas_playas() -> BanderasPlayasOut:
    if (hit := _cacheado("banderas")) is not None:
        return hit  # type: ignore[no-any-return]
    tb = _obtener_cliente()
    dispositivos = await tb.dispositivos(TIPO_BANDERAS)
    atributos = await asyncio.gather(*(tb.atributos("DEVICE", d["id"]["id"]) for d in dispositivos))
    banderas = [
        BanderaPlayaOut(**b)
        for d, a in zip(dispositivos, atributos, strict=True)
        if (b := parsear_bandera(d, a)) is not None
    ]
    resultado = BanderasPlayasOut(
        obtenido_en=datetime.now(UTC), total=len(banderas), banderas=banderas
    )
    _cache["banderas"] = (time.monotonic(), resultado)
    return resultado


async def aforo_parque() -> AforoParqueOut:
    if (hit := _cacheado("aforo")) is not None:
        return hit  # type: ignore[no-any-return]
    tb = _obtener_cliente()
    activos = await tb.activos()
    activo = next((a for a in activos if a.get("name") == ACTIVO_AFORO_PARQUE), None)
    valores: dict[str, Any] = {}
    if activo is not None:
        telemetria = await tb.telemetria_actual("ASSET", activo["id"]["id"], CLAVES_AFORO_PARQUE)
        valores = parsear_aforo_parque(telemetria)
    ts_ms = valores.get("ts_ms")
    resultado = AforoParqueOut(
        obtenido_en=datetime.now(UTC),
        medido_en=datetime.fromtimestamp(ts_ms / 1000, tz=UTC) if ts_ms else None,
        aforo_actual=valores.get("aforo_parque"),
        entradas_hoy=valores.get("entradas_parque"),
        salidas_hoy=valores.get("salidas_parque"),
        total_vehiculos=valores.get("total_parque"),
        total_motorizados=valores.get("total_motorizados"),
        total_no_motorizados=valores.get("total_no_motorizados"),
        total_personas=valores.get("total_personas"),
    )
    _cache["aforo"] = (time.monotonic(), resultado)
    return resultado
