"""Endpoints de apoyo al trabajo de campo de mediciones de cobertura.

Las mediciones con G-NetTrack (puntos P01–P25) necesitan un servidor HTTP
propio y estable — no un enlace de Google Drive con redirecciones y páginas
intermedias — para que la velocidad registrada sea comparable entre puntos:

- ``GET  /cobertura/descarga``  → fichero de prueba de 100 MB (bytes aleatorios,
  incompresibles, sin caché) con ``Content-Length`` fijo.
- ``POST/PUT /cobertura/subida`` → acepta cualquier cuerpo (binario o
  multipart), lo consume en streaming sin guardarlo y devuelve bytes y Mbps.
- ``GET  /cobertura/ping``       → respuesta mínima para latencia.
- ``GET  /cobertura/registro``   → últimas pruebas recibidas (para documentar
  la campaña; requiere sesión del panel).

Ambos endpoints de prueba son públicos por diseño (la app no puede
autenticarse). Si se define ``COBERTURA_TOKEN`` en el ``.env``, exigen ``?k=``
en la URL, que se copia una sola vez en G-NetTrack.
"""

from __future__ import annotations

import os
import time
from collections import deque
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from nijar_dti.api.v1.dependencies import get_current_user
from nijar_dti.config import get_settings
from nijar_dti.core.logging import get_logger
from nijar_dti.schemas.auth import CurrentUser

router = APIRouter()
log = get_logger(__name__)

_MIB = 1024 * 1024
_CHUNK = _MIB
_MB_DEFECTO = 100
_MB_MAXIMO = 500
_SUBIDA_MAX_BYTES = 1024 * _MIB  # 1 GiB por prueba

# Últimas pruebas recibidas (memoria del proceso; suficiente para documentar
# una campaña de campo y se vuelca también al log estructurado).
_registro: deque[dict[str, Any]] = deque(maxlen=500)


def _comprobar_token(k: str | None) -> None:
    esperado = get_settings().cobertura_token
    if esperado and k != esperado:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token de cobertura inválido")


def _ip(request: Request) -> str:
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _anotar(request: Request, tipo: str, n_bytes: int, duracion_s: float) -> dict[str, Any]:
    mbps = round((n_bytes * 8) / duracion_s / 1_000_000, 2) if duracion_s > 0 else None
    fila = {
        "tipo": tipo,
        "ts": datetime.now(UTC).isoformat(),
        "bytes": n_bytes,
        "megabytes": round(n_bytes / _MIB, 2),
        "duracion_ms": int(duracion_s * 1000),
        "mbps": mbps,
        "ip": _ip(request),
        "user_agent": request.headers.get("user-agent", "")[:200],
    }
    _registro.append(fila)
    log.info("cobertura_prueba", **fila)
    return fila


async def _bytes_aleatorios(total: int) -> AsyncIterator[bytes]:
    restante = total
    while restante > 0:
        n = min(_CHUNK, restante)
        yield os.urandom(n)
        restante -= n


@router.get(
    "/descarga",
    summary="Fichero de prueba de descarga (100 MB por defecto)",
    response_class=StreamingResponse,
)
async def descarga(
    request: Request,
    mb: int = Query(_MB_DEFECTO, ge=1, le=_MB_MAXIMO, description="Tamaño en MiB"),
    k: str | None = Query(None, description="Token si COBERTURA_TOKEN está definido"),
) -> StreamingResponse:
    _comprobar_token(k)
    total = mb * _MIB
    inicio = time.monotonic()

    async def cuerpo() -> AsyncIterator[bytes]:
        async for trozo in _bytes_aleatorios(total):
            yield trozo
        _anotar(request, "descarga", total, time.monotonic() - inicio)

    return StreamingResponse(
        cuerpo(),
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(total),
            "Content-Disposition": f'attachment; filename="prueba-{mb}mb.bin"',
            "Cache-Control": "no-store, no-transform",
            "Accept-Ranges": "none",
        },
    )


@router.api_route(
    "/subida",
    methods=["POST", "PUT"],
    summary="Sumidero de subida: acepta cualquier cuerpo y mide el caudal",
)
async def subida(
    request: Request,
    k: str | None = Query(None, description="Token si COBERTURA_TOKEN está definido"),
) -> dict[str, Any]:
    _comprobar_token(k)
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > _SUBIDA_MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="Máximo 1 GiB por prueba")
    inicio = time.monotonic()
    recibidos = 0
    async for trozo in request.stream():
        recibidos += len(trozo)
        if recibidos > _SUBIDA_MAX_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="Máximo 1 GiB por prueba")
    fila = _anotar(request, "subida", recibidos, time.monotonic() - inicio)
    return {"ok": True, **{c: fila[c] for c in ("bytes", "megabytes", "duracion_ms", "mbps")}}


@router.get("/ping", summary="Respuesta mínima para medir latencia")
async def ping() -> dict[str, Any]:
    return {"ok": True, "ts": datetime.now(UTC).isoformat()}


@router.get(
    "/registro",
    summary="Últimas pruebas de descarga/subida recibidas (documentación de campaña)",
)
async def registro(
    limite: int = Query(100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    return list(_registro)[-limite:][::-1]
