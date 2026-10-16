"""Endpoints del gemelo digital: verticales externas (ThingsBoard).

Fase 4 del gemelo — integración de la plataforma IoT municipal existente
(banderas de playa y aforo del P.N. Cabo de Gata). Si ``THINGSBOARD_*`` no
está configurado en el entorno, los endpoints responden 503 y el panel lo
muestra como fuente pendiente (sin datos ficticios).
"""

from __future__ import annotations

import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.config import get_settings
from nijar_dti.connectors.bettair import BettairError
from nijar_dti.connectors.openmeteo import OpenMeteoError
from nijar_dti.connectors.thingsboard import ThingsBoardError
from nijar_dti.schemas.auth import CurrentUser
from nijar_dti.schemas.gemelo import (
    AforoParqueOut,
    BanderasPlayasOut,
    EstacionesAireOut,
    EstadoGemelo,
    MeteoActualOut,
    OrtofotoHistoricaOut,
    OrtofotosHistoricasOut,
    ResumenAireOut,
)
from nijar_dti.services import gemelo_service as svc
from nijar_dti.services import ortofotos_service

router = APIRouter()


def _requiere_thingsboard() -> None:
    if not svc.thingsboard_configurado():
        raise HTTPException(
            status_code=503,
            detail="Vertical ThingsBoard sin configurar (THINGSBOARD_BASE_URL/USUARIO/PASSWORD)",
        )


@router.get("/estado", response_model=EstadoGemelo, summary="Fuentes externas del gemelo")
async def estado(user: CurrentUser = Depends(get_current_user)) -> EstadoGemelo:
    return svc.estado_gemelo()


@router.get(
    "/playas/banderas",
    response_model=BanderasPlayasOut,
    summary="Banderas de playa en tiempo real (ThingsBoard)",
)
async def banderas(user: CurrentUser = Depends(get_current_user)) -> BanderasPlayasOut:
    _requiere_thingsboard()
    try:
        return await svc.banderas_playas()
    except ThingsBoardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/parque/aforo",
    response_model=AforoParqueOut,
    summary="Aforo en tiempo real del P.N. Cabo de Gata (ThingsBoard)",
)
async def aforo(user: CurrentUser = Depends(get_current_user)) -> AforoParqueOut:
    _requiere_thingsboard()
    try:
        return await svc.aforo_parque()
    except ThingsBoardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/meteo",
    response_model=MeteoActualOut,
    summary="Meteorología pública del municipio (Open-Meteo)",
)
async def meteo(
    lat: float | None = Query(None, ge=-90, le=90, description="Latitud (p. ej. la del tótem)"),
    lon: float | None = Query(None, ge=-180, le=180, description="Longitud (p. ej. la del tótem)"),
) -> MeteoActualOut:
    """Condiciones actuales y previsión a 3 días (fuente pública Open-Meteo).
    Con ``lat``/``lon`` devuelve el tiempo de esa ubicación; si no, el de Níjar.
    No requiere credenciales; lo consume el tótem público."""
    try:
        return await svc.meteo_actual(lat, lon)
    except OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/aire/resumen",
    response_model=ResumenAireOut,
    summary="Resumen meteorológico y de calidad del aire del municipio (público)",
)
async def aire_resumen() -> ResumenAireOut:
    """Agregado municipal sin datos sensibles: lo consume el tótem público
    (temperatura, humedad y peor índice EAQI de las estaciones activas)."""
    if not svc.bettair_configurado():
        raise HTTPException(
            status_code=503,
            detail="Vertical Bettair sin configurar (BETTAIR_CLIENT_ID/CLIENT_SECRET)",
        )
    try:
        return await svc.resumen_aire()
    except BettairError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/aire/estaciones",
    response_model=EstacionesAireOut,
    summary="Estaciones de calidad del aire y meteorología (Bettair)",
)
async def aire(user: CurrentUser = Depends(get_current_user)) -> EstacionesAireOut:
    if not svc.bettair_configurado():
        raise HTTPException(
            status_code=503,
            detail="Vertical Bettair sin configurar (BETTAIR_CLIENT_ID/CLIENT_SECRET)",
        )
    try:
        return await svc.estaciones_aire()
    except BettairError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/ortofotos-historicas",
    response_model=OrtofotosHistoricasOut,
    summary="Ortofotos históricas de Níjar (IGN y Junta de Andalucía) para el selector de periodo",
)
async def ortofotos_historicas(
    user: CurrentUser = Depends(get_current_user),
) -> OrtofotosHistoricasOut:
    """Vuelos disponibles (1956 → actualidad) con imagen sobre el municipio: PNOA
    histórico del IGN y vuelos de la Junta (REDIAM e IECA), en orden cronológico."""
    ign_res, (vuelos_junta, _) = await asyncio.gather(
        _ign_o_none(), ortofotos_service.listar_ortofotos_junta()
    )
    if ign_res is None and not vuelos_junta:
        raise HTTPException(
            status_code=502, detail="Servicios de ortofotos históricas (IGN y Junta) no disponibles"
        )
    url, capas, verificada = ign_res or (get_settings().ortofoto_historica_wms_url, [], True)
    salida = [
        OrtofotoHistoricaOut(
            nombre=o.nombre, titulo=o.titulo, anio=o.anio, etiqueta=o.etiqueta, id=f"ign:{o.nombre}"
        )
        for o in capas
    ] + [
        OrtofotoHistoricaOut(
            nombre=o.capa,
            titulo=o.titulo,
            anio=o.anio,
            etiqueta=o.etiqueta,
            id=o.id,
            fuente=f"Junta de Andalucía · {o.organismo}",
            url_wms=o.url,
            version="1.1.1",
            formato=o.formato,
        )
        for o in vuelos_junta
    ]
    salida.sort(key=lambda o: (o.anio, o.fuente != "IGN", o.etiqueta))
    return OrtofotosHistoricasOut(url_wms=url, cobertura_verificada=verificada, capas=salida)


async def _ign_o_none() -> tuple[str, list[ortofotos_service.OrtofotoHistorica], bool] | None:
    try:
        return await ortofotos_service.listar_ortofotos()
    except httpx.HTTPError:
        return None
