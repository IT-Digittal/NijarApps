"""Aplicación FastAPI principal de la Plataforma DTI Níjar.

Punto de entrada de la API REST que expone los servicios DTI Smart City
del Ayuntamiento de Níjar conforme a la norma UNE 178104.
"""

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from nijar_dti.api.v1.router import api_router
from nijar_dti.config import get_settings
from nijar_dti.core.logging import configure_logging, get_logger
from nijar_dti.core.metrics import (
    http_request_duration_seconds,
    http_requests_total,
    metrics_endpoint,
    metrics_loop,
)
from nijar_dti.schemas.common import APIError

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida de la aplicación: arranque y cierre limpio."""
    logger.info(
        "Arrancando plataforma DTI Níjar",
        version=settings.app_version,
        env=settings.app_env,
    )
    # Carga idempotente de datos seed (recursos, sensores, FAQs, demo C.1).
    # Solo añade lo que falte; no toca filas existentes.
    if settings.run_seeds_on_startup:
        logger.info("Ejecutando seed_loader idempotente al arranque")
        try:
            from nijar_dti.data.seed_loader import run as seed_run

            await seed_run()
            logger.info("seed_loader completado")
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo en seed_loader durante el arranque", error=str(exc))
    # Refresco periódico de métricas Prometheus de dominio
    metrics_task = asyncio.create_task(metrics_loop(interval_seconds=60))
    try:
        yield
    finally:
        metrics_task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await metrics_task
        logger.info("Cerrando plataforma DTI Níjar")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Plataforma de Destino Turístico Inteligente (DTI) Smart City "
        "del Ayuntamiento de Níjar. Conforme a UNE 178104, FIWARE Smart "
        "Data Models y ENS Nivel Medio."
    ),
    contact={
        "name": "IT DIGITTAL",
        "url": "https://www.turismonijar.es",
    },
    license_info={
        "name": "Propiedad del Ayuntamiento de Níjar",
        "url": "https://www.nijar.es",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# CORS — orígenes permitidos definidos en la configuración
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Montar router principal
app.include_router(api_router, prefix="/api/v1")


# Middleware: cuenta peticiones y mide latencias para Prometheus.
@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        # Usamos route.path si lo conocemos, para evitar cardinalidad alta
        # con IDs en la URL. Si no, usamos el path tal cual.
        path = request.scope.get("route").path if request.scope.get("route") else request.url.path
        method = request.method
        try:
            http_requests_total.labels(method=method, path=path, status=str(status_code)).inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(elapsed)
        except Exception:  # noqa: BLE001, S110
            # Una métrica no debe romper la respuesta. Silenciar es seguro.
            pass


# Endpoint Prometheus
app.add_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)


# Servir el dashboard estático en /dashboard si la carpeta frontend está
# disponible junto al despliegue. En docker-compose se monta como volumen.
import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles


def _buscar_frontend() -> Path | None:
    """Localiza la carpeta frontend/ según el modo de despliegue.

    - FRONTEND_DIR: override explícito por variable de entorno.
    - Relativa al código fuente: desarrollo (repo clonado o volumen en /app/src).
    - Relativa al directorio de trabajo: imagen Docker de producción, donde el
      paquete se instala en site-packages pero frontend/ se copia a /app.
    """
    override = os.environ.get("FRONTEND_DIR")
    candidatos = [Path(override)] if override else []
    candidatos += [
        Path(__file__).resolve().parent.parent.parent / "frontend",
        Path.cwd() / "frontend",
    ]
    for candidato in candidatos:
        if candidato.is_dir():
            return candidato
    return None


_frontend_base = _buscar_frontend()
if _frontend_base is None:
    logger.warning("Carpeta frontend/ no encontrada — dashboard y tótem no disponibles")
else:
    for _ruta, _subdir, _html in (
        ("/dashboard", "dashboard", True),
        ("/shared", "shared", False),
        ("/totem", "totem", True),
    ):
        _dir = _frontend_base / _subdir
        if _dir.is_dir():
            app.mount(_ruta, StaticFiles(directory=str(_dir), html=_html), name=_subdir)
            logger.info("Frontend estático montado", ruta=_ruta, path=str(_dir))


# ----------------- Manejo global de excepciones -----------------
# Los errores se mapean al esquema APIError uniforme (schemas/common.py).


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> ORJSONResponse:
    code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }.get(exc.status_code, "ERROR")
    body = APIError(code=code, message=str(exc.detail))
    return ORJSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    body = APIError(
        code="VALIDATION_ERROR",
        message="La petición no cumple el esquema esperado",
        details={"errors": exc.errors()},
    )
    return ORJSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    logger.exception("Error no controlado", path=str(request.url), error=str(exc))
    body = APIError(
        code="INTERNAL_ERROR",
        message="Error interno del servicio",
    )
    return ORJSONResponse(status_code=500, content=body.model_dump())


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Endpoint raíz: redirige a la documentación."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
