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

from nijar_dti.models.alumbrado import CuadroMando, Luminaria, ZonaAlumbrado
from nijar_dti.models.campana import Campana
from nijar_dti.models.cliente import Cliente
from nijar_dti.models.consumo_ia import ConsumoIA
from nijar_dti.models.contenido import Contenido
from nijar_dti.models.contexto import ContextoTuristico
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.faq import FAQ, InteraccionChatbot
from nijar_dti.models.fuente_dato import FuenteDato
from nijar_dti.models.incidencia import Incidencia
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.recomendacion_direccion import RecomendacionDireccion
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.rol import Rol
from nijar_dti.models.sensor import Sensor
from nijar_dti.models.servicio import Servicio
from nijar_dti.models.usuario import Usuario
from nijar_dti.models.verticales import (
    CamaraCCTV,
    Contenedor,
    PuntoMovilidad,
    SectorAgua,
    SuministroEnergia,
)
from nijar_dti.models.visita import Visita

__all__ = [
    "FAQ",
    "CamaraCCTV",
    "Campana",
    "Cliente",
    "Contenedor",
    "Contenido",
    "ContextoTuristico",
    "CuadroMando",
    "EventoTuristico",
    "FuenteDato",
    "Incidencia",
    "InteraccionChatbot",
    "Luminaria",
    "Observacion",
    "Opinion",
    "PuntoMovilidad",
    "RecomendacionDireccion",
    "RecursoTuristico",
    "Rol",
    "SectorAgua",
    "Sensor",
    "Servicio",
    "SuministroEnergia",
    "Usuario",
    "Visita",
    "ZonaAlumbrado",
]
