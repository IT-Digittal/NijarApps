"""Router maestro que agrupa todos los endpoints de la API v1."""

from fastapi import APIRouter

from nijar_dti.api.v1 import (
    auth,
    campanas,
    chatbot,
    cliente,
    cms,
    contexto,
    dashboards,
    direccion,
    documentos,
    fuentes,
    gemelo,
    health,
    incidencias,
    iot,
    prediccion,
    roles,
    rutas,
    social,
    tourism,
    usuarios,
    verticales,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tourism.router, prefix="/tourism", tags=["tourism"])
api_router.include_router(iot.router, prefix="/data/iot", tags=["iot"])
api_router.include_router(social.router, prefix="/data/social", tags=["social-listening"])
api_router.include_router(contexto.router, prefix="/data/contexto", tags=["contexto"])
api_router.include_router(prediccion.router, prefix="/prediccion", tags=["prediccion"])
api_router.include_router(rutas.router, prefix="/rutas", tags=["rutas"])
api_router.include_router(incidencias.router, prefix="/incidencias", tags=["incidencias"])
api_router.include_router(cms.router, prefix="/cms", tags=["cms"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(cliente.router, prefix="/cliente", tags=["cliente"])
api_router.include_router(campanas.router, prefix="/campanas", tags=["campanas"])
api_router.include_router(verticales.router, prefix="/verticales", tags=["verticales"])
api_router.include_router(fuentes.router, prefix="/integraciones", tags=["integraciones"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(direccion.router, prefix="/direccion", tags=["direccion"])
api_router.include_router(gemelo.router, prefix="/gemelo", tags=["gemelo"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
