"""Script CLI para cargar los datos seed iniciales.

Uso:
    python -m nijar_dti.data.seed_loader

Es idempotente: detecta entradas existentes (por URN/email/intent) y no las
duplica. Diseñado para ejecutarse tras `alembic upgrade head` en la primera
puesta en producción y en los entornos de desarrollo y staging.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.data.seeds.admin_user import ADMIN_USER_SEED, admin_password_hash
from nijar_dti.data.seeds.faqs import FAQS_SEED
from nijar_dti.data.seeds.recursos_turisticos import RECURSOS_SEED
from nijar_dti.data.seeds.sensores import SENSORES_SEED
from nijar_dti.data.seeds.demo_data import (
    generar_eventos_seed,
    generar_interacciones_chatbot_seed,
    generar_observaciones_seed,
    generar_opiniones_seed,
    generar_visitas_totem_seed,
)
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.faq import FAQ, InteraccionChatbot, NivelConfianza
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.sensor import Sensor
from nijar_dti.models.usuario import Usuario
from nijar_dti.models.visita import Visita


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("nijar_dti.seed")


def _wkt(lon: float, lat: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


async def seed_admin_user(db: AsyncSession) -> None:
    email = ADMIN_USER_SEED["email"]
    res = await db.execute(select(Usuario).where(Usuario.email == email))
    if res.scalar_one_or_none() is not None:
        log.info("Admin user '%s' ya existe — saltando", email)
        return
    user = Usuario(
        email=email,
        nombre_completo=ADMIN_USER_SEED["nombre_completo"],
        password_hash=admin_password_hash(),
        rol=ADMIN_USER_SEED["rol"],
        activo=ADMIN_USER_SEED["activo"],
        requiere_2fa=ADMIN_USER_SEED["requiere_2fa"],
        scopes_adicionales=list(ADMIN_USER_SEED.get("scopes_adicionales") or []),
    )
    db.add(user)
    log.info("Admin user creado: %s", email)


async def seed_recursos(db: AsyncSession) -> None:
    creados = 0
    for r in RECURSOS_SEED:
        urn = r["urn"]
        existente = (
            await db.execute(select(RecursoTuristico).where(RecursoTuristico.urn == urn))
        ).scalar_one_or_none()
        if existente is not None:
            continue
        obj = RecursoTuristico(
            urn=urn,
            nombre=r["nombre"],
            categoria=r["categoria"],
            descripcion_corta=r.get("descripcion_corta"),
            nombre_i18n=r.get("nombre_i18n"),
            descripcion_i18n=r.get("descripcion_i18n"),
            ubicacion=_wkt(r["lon"], r["lat"]),
            municipio="Níjar",
            telefono=r.get("telefono"),
            horario=r.get("horario"),
            servicios_disponibles=r.get("servicios_disponibles"),
            etiquetas=r.get("etiquetas"),
            activo=True,
            publicado=r.get("publicado", False),
        )
        db.add(obj)
        creados += 1
    log.info("Recursos turísticos creados: %d", creados)


async def seed_sensores(db: AsyncSession) -> None:
    creados = 0
    for s in SENSORES_SEED:
        urn = s["urn"]
        existente = (
            await db.execute(select(Sensor).where(Sensor.urn == urn))
        ).scalar_one_or_none()
        if existente is not None:
            continue
        obj = Sensor(
            urn=urn,
            nombre=s["nombre"],
            tipo=s["tipo"],
            fabricante=s.get("fabricante"),
            modelo=s.get("modelo"),
            ubicacion=_wkt(s["lon"], s["lat"]),
            descripcion_ubicacion=s.get("descripcion_ubicacion"),
            unidades_medida=s.get("unidades_medida"),
            rango_minimo=s.get("rango_minimo"),
            rango_maximo=s.get("rango_maximo"),
            umbrales_alerta=s.get("umbrales_alerta"),
            frecuencia_muestreo_seg=s.get("frecuencia_muestreo_seg"),
            estado=s.get("estado", "operativo"),
            topic_mqtt=s.get("topic_mqtt"),
            etiquetas=s.get("etiquetas"),
            activo=True,
        )
        db.add(obj)
        creados += 1
    log.info("Sensores creados: %d", creados)


async def seed_faqs(db: AsyncSession) -> None:
    creadas = 0
    for f in FAQS_SEED:
        intent = f["intent"]
        existente = (
            await db.execute(select(FAQ).where(FAQ.intent == intent))
        ).scalar_one_or_none()
        if existente is not None:
            continue
        nivel = f.get("nivel_confianza", "alta")
        try:
            nivel_enum = NivelConfianza(nivel)
        except ValueError:
            nivel_enum = NivelConfianza.ALTA
        obj = FAQ(
            intent=intent,
            categoria=f["categoria"],
            pregunta_es=f["pregunta_es"],
            pregunta_en=f.get("pregunta_en"),
            pregunta_de=f.get("pregunta_de"),
            pregunta_fr=f.get("pregunta_fr"),
            frases_entrenamiento_es=f.get("frases_entrenamiento_es"),
            frases_entrenamiento_en=f.get("frases_entrenamiento_en"),
            frases_entrenamiento_de=f.get("frases_entrenamiento_de"),
            frases_entrenamiento_fr=f.get("frases_entrenamiento_fr"),
            respuesta_es=f["respuesta_es"],
            respuesta_en=f.get("respuesta_en"),
            respuesta_de=f.get("respuesta_de"),
            respuesta_fr=f.get("respuesta_fr"),
            nivel_confianza=nivel_enum,
            fuente_url=f.get("fuente_url"),
            fuente_descripcion=f.get("fuente_descripcion"),
            activo=True,
            version=1,
        )
        db.add(obj)
        creadas += 1
    log.info("FAQs creadas: %d", creadas)


async def seed_demo_eventos(db: AsyncSession) -> None:
    """Carga eventos turísticos de demo si no existen."""
    from sqlalchemy import func as sqlfunc
    count = int((await db.execute(select(sqlfunc.count()).select_from(EventoTuristico))).scalar_one() or 0)
    if count > 0:
        log.info("Ya hay %d eventos — saltando demo eventos", count)
        return
    datos = generar_eventos_seed()
    for d in datos:
        db.add(EventoTuristico(**d))
    log.info("Eventos demo creados: %d", len(datos))


async def seed_demo_observaciones(db: AsyncSession) -> None:
    """Carga observaciones IoT de demo si no existen."""
    from sqlalchemy import func as sqlfunc
    count = int((await db.execute(select(sqlfunc.count()).select_from(Observacion))).scalar_one() or 0)
    if count > 0:
        log.info("Ya hay %d observaciones — saltando demo IoT", count)
        return
    # Obtener IDs de sensores ambientales
    sensores = (await db.execute(select(Sensor).where(Sensor.deleted_at.is_(None)))).scalars().all()
    sensores_por_tipo: dict[str, str] = {}
    for s in sensores:
        if s.tipo in ("ambiental_co2", "ambiental_temperatura", "ambiental_humedad", "ambiental_ruido"):
            sensores_por_tipo[s.tipo] = str(s.id)
    if not sensores_por_tipo:
        log.warning("No se encontraron sensores ambientales para demo")
        return
    datos = generar_observaciones_seed(sensores_por_tipo)
    for d in datos:
        db.add(Observacion(**d))
    log.info("Observaciones IoT demo creadas: %d", len(datos))


async def seed_demo_opiniones(db: AsyncSession) -> None:
    """Carga opiniones de social listening de demo si no existen."""
    from sqlalchemy import func as sqlfunc
    count = int((await db.execute(select(sqlfunc.count()).select_from(Opinion))).scalar_one() or 0)
    if count > 0:
        log.info("Ya hay %d opiniones — saltando demo social", count)
        return
    datos = generar_opiniones_seed()
    for d in datos:
        db.add(Opinion(**d))
    log.info("Opiniones demo creadas: %d", len(datos))


async def seed_demo_visitas_totem(db: AsyncSession) -> None:
    """Carga visitas de tótem de demo si no existen."""
    from sqlalchemy import func as sqlfunc
    count = int((await db.execute(select(sqlfunc.count()).select_from(Visita))).scalar_one() or 0)
    if count > 0:
        log.info("Ya hay %d visitas — saltando demo tótems", count)
        return
    datos = generar_visitas_totem_seed()
    for d in datos:
        db.add(Visita(**d))
    log.info("Visitas tótem demo creadas: %d", len(datos))


async def seed_demo_chatbot(db: AsyncSession) -> None:
    """Carga interacciones de chatbot de demo si no existen."""
    from sqlalchemy import func as sqlfunc
    count = int((await db.execute(select(sqlfunc.count()).select_from(InteraccionChatbot))).scalar_one() or 0)
    if count > 0:
        log.info("Ya hay %d interacciones chatbot — saltando demo", count)
        return
    datos = generar_interacciones_chatbot_seed()
    for d in datos:
        db.add(InteraccionChatbot(**d))
    log.info("Interacciones chatbot demo creadas: %d", len(datos))


async def run() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await seed_admin_user(db)
            await seed_recursos(db)
            await seed_sensores(db)
            await seed_faqs(db)
            await db.flush()
            # Demo data (solo si las tablas están vacías)
            await seed_demo_eventos(db)
            await seed_demo_observaciones(db)
            await seed_demo_opiniones(db)
            await seed_demo_visitas_totem(db)
            await seed_demo_chatbot(db)
            await db.commit()
            log.info("Seeds aplicados correctamente")
        except Exception:  # noqa: BLE001
            await db.rollback()
            log.exception("Error aplicando seeds — rollback")
            raise


def main() -> None:
    try:
        asyncio.run(run())
    except Exception:  # noqa: BLE001
        sys.exit(1)


if __name__ == "__main__":
    main()
