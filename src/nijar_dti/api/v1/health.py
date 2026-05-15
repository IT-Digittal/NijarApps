"""Endpoints de health check y readiness."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.core.database import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Indica si la API está viva (responde a peticiones).",
)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Verifica que la API y sus dependencias críticas (BBDD) están operativas.",
)
async def ready(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {type(exc).__name__}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return ReadinessResponse(status=overall, checks=checks)


class VersionResponse(BaseModel):
    """Metadata operativa de la API.

    Útil para el SOC y para que los integradores externos verifiquen
    qué versión de la plataforma están consumiendo.
    """

    name: str
    version: str
    environment: str
    chatbot_engine: str
    expediente: str = "18962/2025"
    adjudicatario: str = "IT DIGITTAL"
    marco: str = "PRTR-NextGenerationEU-C14"


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Metadata operativa",
    description="Devuelve la versión, entorno y motor del chatbot activo. Útil para auditoría.",
)
async def version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        chatbot_engine=settings.chatbot_engine,
    )
