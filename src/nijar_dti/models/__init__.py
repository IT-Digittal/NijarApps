"""Modelos ORM (SQLAlchemy 2.0) basados en FIWARE Smart Data Models.

Entidades del modelo semántico de la plataforma DTI Níjar:
- RecursoTuristico (POIs, playas, monumentos, rutas)
- EventoTuristico
- Servicio (alojamiento, gastronomía, etc.)
- Sensor + Observacion (telemetría IoT)
- Visita (interacciones / proximidad)
- Opinion (menciones RRSS, reseñas)
- Usuario (RBAC)
"""

from nijar_dti.models.contenido import Contenido
from nijar_dti.models.contexto import ContextoTuristico
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.faq import FAQ, InteraccionChatbot
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.sensor import Sensor
from nijar_dti.models.servicio import Servicio
from nijar_dti.models.usuario import Usuario
from nijar_dti.models.visita import Visita

__all__ = [
    "FAQ",
    "Contenido",
    "ContextoTuristico",
    "EventoTuristico",
    "InteraccionChatbot",
    "Observacion",
    "Opinion",
    "RecursoTuristico",
    "Sensor",
    "Servicio",
    "Usuario",
    "Visita",
]
