"""Router maestro que agrupa todos los endpoints de la API v1."""

from fastapi import APIRouter

from nijar_dti.api.v1 import (
    auth,
    chatbot,
    cms,
    dashboards,
    health,
    iot,
    social,
    tourism,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tourism.router, prefix="/tourism", tags=["tourism"])
api_router.include_router(iot.router, prefix="/data/iot", tags=["iot"])
api_router.include_router(social.router, prefix="/data/social", tags=["social-listening"])
api_router.include_router(cms.router, prefix="/cms", tags=["cms"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
