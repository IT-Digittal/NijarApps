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
from datetime import UTC

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core import permisos as permisos_catalogo
from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.data.seeds.admin_user import (
    ADMIN_USER_SEED,
    DIRECCION_USER_SEED,
    admin_password_hash,
    direccion_password_hash,
)
from nijar_dti.data.seeds.campanas import generar_campanas_seed
from nijar_dti.data.seeds.cliente import CLIENTE_SEED
from nijar_dti.data.seeds.demo_data import (
    generar_contenidos_seed,
    generar_eventos_seed,
    generar_incidencias_seed,
    generar_interacciones_chatbot_seed,
    generar_observaciones_seed,
    generar_observaciones_totem_seed,
    generar_opiniones_seed,
    generar_visitas_totem_seed,
    generar_visitas_web_app_seed,
)
from nijar_dti.data.seeds.faqs import FAQS_SEED
from nijar_dti.data.seeds.fuentes_datos import FUENTES_DATOS_SEED
from nijar_dti.data.seeds.historico_verticales import generar_historico_seed
from nijar_dti.data.seeds.publicidad import EMPRESAS_SEED
from nijar_dti.data.seeds.recursos_turisticos import RECURSOS_SEED
from nijar_dti.data.seeds.sensores import SENSORES_SEED
from nijar_dti.data.seeds.verticales import (
    COORDS_CAMARAS,
    COORDS_MOVILIDAD,
    UMBRAL_LON_MAR,
    ZONAS_ALUMBRADO,
    generar_camaras_seed,
    generar_contenedores_seed,
    generar_cuadros_seed,
    generar_luminarias_seed,
    generar_movilidad_seed,
    generar_sectores_agua_seed,
    generar_suministros_energia_seed,
)
from nijar_dti.models.alumbrado import CuadroMando, Luminaria, ZonaAlumbrado
from nijar_dti.models.campana import Campana
from nijar_dti.models.cliente import Cliente
from nijar_dti.models.contenido import Contenido
from nijar_dti.models.contexto import ContextoTuristico
from nijar_dti.models.empresa_anunciante import EmpresaAnunciante
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.faq import FAQ, InteraccionChatbot, NivelConfianza
from nijar_dti.models.fuente_dato import FuenteDato
from nijar_dti.models.incidencia import Incidencia
from nijar_dti.models.metrica_historica import MetricaHistorica
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.rol import Rol
from nijar_dti.models.sensor import Sensor
from nijar_dti.models.usuario import Usuario
from nijar_dti.models.verticales import (
    CamaraCCTV,
    Contenedor,
    PuntoMovilidad,
    SectorAgua,
    SuministroEnergia,
)
from nijar_dti.models.visita import Visita

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("nijar_dti.seed")


def _wkt(lon: float, lat: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


async def _seed_usuario(db: AsyncSession, seed: dict, password_hash: str) -> None:
    """Crea un usuario del seed si no existe (idempotente por email)."""
    email = seed["email"]
    res = await db.execute(select(Usuario).where(Usuario.email == email))
    if res.scalar_one_or_none() is not None:
        log.info("Usuario '%s' ya existe — saltando", email)
        return
    user = Usuario(
        email=email,
        nombre_completo=seed["nombre_completo"],
        password_hash=password_hash,
        rol=seed["rol"],
        activo=seed["activo"],
        requiere_2fa=seed["requiere_2fa"],
        scopes_adicionales=list(seed.get("scopes_adicionales") or []),
    )
    db.add(user)
    log.info("Usuario creado: %s (%s)", email, seed["rol"])


async def seed_admin_user(db: AsyncSession) -> None:
    await _seed_usuario(db, ADMIN_USER_SEED, admin_password_hash())
    await _seed_usuario(db, DIRECCION_USER_SEED, direccion_password_hash())


async def seed_roles(db: AsyncSession) -> None:
    """Siembra los roles integrados en la tabla `roles` (idempotente por tabla).

    Los permisos por defecto salen del catálogo curado en `core.permisos`; una
    vez sembrados, la BD es la fuente de verdad y el administrador puede
    editarlos o crear roles nuevos desde el panel.
    """
    from sqlalchemy import func as sqlfunc

    n = int((await db.execute(select(sqlfunc.count()).select_from(Rol))).scalar_one() or 0)
    if n > 0:
        log.info("Roles ya existen (%d) — saltando", n)
        return
    for slug, permisos in permisos_catalogo.PERMISOS_POR_ROL.items():
        db.add(
            Rol(
                slug=slug,
                display=permisos_catalogo.DISPLAY_ROLES.get(slug, slug),
                descripcion=None,
                permisos=sorted(permisos),
                es_sistema=True,
            )
        )
    log.info("Roles integrados creados: %d", len(permisos_catalogo.PERMISOS_POR_ROL))


async def seed_recursos(db: AsyncSession) -> None:
    from sqlalchemy import func as sqlfunc

    creados = 0
    traducciones_actualizadas = 0
    coordenadas_actualizadas = 0
    for r in RECURSOS_SEED:
        urn = r["urn"]
        existente = (
            await db.execute(select(RecursoTuristico).where(RecursoTuristico.urn == urn))
        ).scalar_one_or_none()
        if existente is not None:
            # Refrescar coordenadas si difieren del seed (>1 m): versiones
            # anteriores tenían varios recursos desplazados (dos caían al mar).
            if existente.ubicacion is not None:
                coincide = (
                    await db.execute(
                        select(
                            sqlfunc.ST_DWithin(
                                RecursoTuristico.ubicacion,
                                sqlfunc.ST_GeographyFromText(
                                    f"SRID=4326;POINT({r['lon']} {r['lat']})"
                                ),
                                1.0,
                            )
                        ).where(RecursoTuristico.urn == urn)
                    )
                ).scalar()
                if not coincide:
                    existente.ubicacion = _wkt(r["lon"], r["lat"])  # type: ignore[assignment]
                    coordenadas_actualizadas += 1
            # Refrescar traducciones si el seed las incorpora y faltan/difieren.
            # Se limita a los campos i18n para evitar sobreescribir contenido
            # editado desde el CMS.
            cambios = False
            nuevo_nombre_i18n = r.get("nombre_i18n")
            nuevo_desc_i18n = r.get("descripcion_i18n")
            if nuevo_nombre_i18n and existente.nombre_i18n != nuevo_nombre_i18n:
                existente.nombre_i18n = nuevo_nombre_i18n
                cambios = True
            if nuevo_desc_i18n and existente.descripcion_i18n != nuevo_desc_i18n:
                existente.descripcion_i18n = nuevo_desc_i18n
                cambios = True
            if cambios:
                traducciones_actualizadas += 1
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
    log.info(
        "Recursos turísticos creados: %d · traducciones: %d · coordenadas corregidas: %d",
        creados,
        traducciones_actualizadas,
        coordenadas_actualizadas,
    )


async def seed_sensores(db: AsyncSession) -> None:
    creados = 0
    for s in SENSORES_SEED:
        urn = s["urn"]
        existente = (await db.execute(select(Sensor).where(Sensor.urn == urn))).scalar_one_or_none()
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
        existente = (await db.execute(select(FAQ).where(FAQ.intent == intent))).scalar_one_or_none()
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


EVENTO_DEMO_URN_PREFIX = "urn:ngsi-ld:EventoTuristico:nijar:"


async def seed_demo_eventos(db: AsyncSession) -> None:
    """Carga o refresca eventos turísticos demo.

    - Limpia primero eventos huérfanos: aquellos con el prefijo URN del seed demo
      (``urn:ngsi-ld:EventoTuristico:nijar:``) cuya URN ya no está en el seed
      actual y cuya ``fecha_fin`` ya pasó. Sin esto, un cambio en el seed dejaba
      los eventos antiguos colgados en la BD.
    - Inserta los eventos del seed actual que falten.
    - Si los que ya existen están todos pasados, refresca fechas e i18n.
    """
    from datetime import datetime

    datos = generar_eventos_seed()
    urns_demo = [d["urn"] for d in datos]
    ahora = datetime.now(UTC)

    # (0) Limpieza de huérfanos: eventos demo que ya no están en el seed y han terminado.
    huerfanos = (
        (
            await db.execute(
                select(EventoTuristico).where(
                    EventoTuristico.urn.like(EVENTO_DEMO_URN_PREFIX + "%"),
                    EventoTuristico.urn.notin_(urns_demo),
                    EventoTuristico.fecha_fin < ahora,
                )
            )
        )
        .scalars()
        .all()
    )
    for e in huerfanos:
        await db.delete(e)
    if huerfanos:
        log.info("Eventos demo huérfanos eliminados: %d", len(huerfanos))

    # (1) Insertar o refrescar los eventos del seed actual.
    existentes = {
        e.urn: e
        for e in (
            await db.execute(select(EventoTuristico).where(EventoTuristico.urn.in_(urns_demo)))
        )
        .scalars()
        .all()
    }
    hay_futuros = any(e.fecha_fin > ahora for e in existentes.values())
    creados = actualizados = 0
    for d in datos:
        e = existentes.get(d["urn"])
        if e is None:
            db.add(EventoTuristico(**d))
            creados += 1
        elif not hay_futuros:
            # Todos los eventos del seed están pasados: refrescar fechas + i18n.
            e.fecha_inicio = d["fecha_inicio"]
            e.fecha_fin = d["fecha_fin"]
            e.nombre_i18n = d.get("nombre_i18n")
            e.descripcion_i18n = d.get("descripcion_i18n")
            actualizados += 1

    if creados:
        log.info("Eventos demo creados: %d", creados)
    if actualizados:
        log.info("Eventos demo refrescados: %d (fechas + i18n)", actualizados)
    if not creados and not actualizados and existentes and hay_futuros:
        vivos = sum(1 for e in existentes.values() if e.fecha_fin > ahora)
        log.info("Eventos demo tienen futuros (%d/%d) — saltando", vivos, len(existentes))


async def seed_demo_observaciones(db: AsyncSession) -> None:
    """Carga observaciones IoT de demo si no existen."""
    from sqlalchemy import func as sqlfunc

    count = int(
        (await db.execute(select(sqlfunc.count()).select_from(Observacion))).scalar_one() or 0
    )
    if count > 0:
        log.info("Ya hay %d observaciones — saltando demo IoT", count)
        return
    # Obtener IDs de sensores ambientales
    sensores = (await db.execute(select(Sensor).where(Sensor.deleted_at.is_(None)))).scalars().all()
    sensores_por_tipo: dict[str, str] = {}
    for s in sensores:
        if s.tipo in (
            "ambiental_co2",
            "ambiental_temperatura",
            "ambiental_humedad",
            "ambiental_ruido",
        ):
            sensores_por_tipo[s.tipo] = str(s.id)
    if not sensores_por_tipo:
        log.warning("No se encontraron sensores ambientales para demo")
        return
    datos = generar_observaciones_seed(sensores_por_tipo)
    for d in datos:
        db.add(Observacion(**d))
    log.info("Observaciones IoT demo creadas: %d", len(datos))


async def seed_demo_observaciones_totem(db: AsyncSession) -> None:
    """Carga telemetría de salud de los tótems si no existe."""
    from sqlalchemy import func as sqlfunc

    sensores = (
        (
            await db.execute(
                select(Sensor).where(Sensor.tipo == "totem", Sensor.deleted_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    if not sensores:
        log.info("No hay sensores de tótem — saltando telemetría de tótems")
        return
    ids = [s.id for s in sensores]
    existentes = int(
        (
            await db.execute(
                select(sqlfunc.count())
                .select_from(Observacion)
                .where(Observacion.sensor_id.in_(ids))
            )
        ).scalar_one()
        or 0
    )
    if existentes > 0:
        log.info("Ya hay %d observaciones de tótem — saltando telemetría", existentes)
        return
    sensores_totem = {s.urn: str(s.id) for s in sensores}
    datos = generar_observaciones_totem_seed(sensores_totem)
    for d in datos:
        db.add(Observacion(**d))
    log.info("Telemetría de tótems demo creada: %d", len(datos))


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

    count = int(
        (await db.execute(select(sqlfunc.count()).select_from(InteraccionChatbot))).scalar_one()
        or 0
    )
    if count > 0:
        log.info("Ya hay %d interacciones chatbot — saltando demo", count)
        return
    datos = generar_interacciones_chatbot_seed()
    for d in datos:
        db.add(InteraccionChatbot(**d))
    log.info("Interacciones chatbot demo creadas: %d", len(datos))


async def seed_contexto_backfill(db: AsyncSession) -> None:
    """Backfill de contexto (INE/Junta/AENA) en dry-run si la tabla está vacía."""
    from sqlalchemy import func as sqlfunc

    count = int(
        (await db.execute(select(sqlfunc.count()).select_from(ContextoTuristico))).scalar_one() or 0
    )
    if count > 0:
        log.info("Ya hay %d registros de contexto — saltando backfill", count)
        return
    from nijar_dti.schemas.contexto import ContextoRecordIn
    from nijar_dti.services.contexto_service import ingerir_registros
    from nijar_dti.workers.contexto_backfill import generar_dataset

    dataset = generar_dataset(dry_run=True, anios=3)
    registros = [ContextoRecordIn(**r) for r in dataset["registros"]]
    result = await ingerir_registros(db, registros)
    log.info(
        "Contexto backfill: insertados=%d actualizados=%d",
        result.insertados,
        result.actualizados,
    )


async def seed_demo_incidencias(db: AsyncSession) -> None:
    """Carga incidencias de mantenimiento de demo (mes anterior) si no existen."""
    from sqlalchemy import func as sqlfunc

    count = int(
        (await db.execute(select(sqlfunc.count()).select_from(Incidencia))).scalar_one() or 0
    )
    if count > 0:
        log.info("Ya hay %d incidencias — saltando demo C.1", count)
        return
    datos = generar_incidencias_seed()
    for d in datos:
        db.add(Incidencia(**d))
    log.info("Incidencias demo creadas: %d", len(datos))


async def seed_cliente(db: AsyncSession) -> None:
    """Carga la ficha general del cliente / Ayuntamiento (bloque 1)."""
    nombre = CLIENTE_SEED["nombre"]
    existente = (
        await db.execute(select(Cliente).where(Cliente.nombre == nombre))
    ).scalar_one_or_none()
    if existente is not None:
        log.info("Ficha de cliente '%s' ya existe — saltando", nombre)
        return
    db.add(Cliente(**CLIENTE_SEED))
    log.info("Ficha de cliente creada: %s", nombre)


async def _recursos_por_urn(db: AsyncSession) -> dict[str, str]:
    """Devuelve un mapa urn -> id (str) de los recursos turísticos vivos."""
    recursos = (
        (await db.execute(select(RecursoTuristico).where(RecursoTuristico.deleted_at.is_(None))))
        .scalars()
        .all()
    )
    return {r.urn: str(r.id) for r in recursos}


async def seed_campanas(db: AsyncSession) -> None:
    """Carga las campañas de promoción turística (bloque 9)."""
    por_urn = await _recursos_por_urn(db)
    creadas = 0
    for c in generar_campanas_seed():
        slug = c["slug"]
        existente = (
            await db.execute(select(Campana).where(Campana.slug == slug))
        ).scalar_one_or_none()
        if existente is not None:
            continue
        recurso_urn = c.pop("recurso_urn", None)
        recurso_id = por_urn.get(recurso_urn) if recurso_urn else None
        db.add(Campana(recurso_id=recurso_id, **c))
        creadas += 1
    log.info("Campañas creadas: %d", creadas)


async def seed_demo_visitas_web_app(db: AsyncSession) -> None:
    """Carga visitas web/app, WiFi y BLE de demo si no existen."""
    from sqlalchemy import func as sqlfunc

    count = int(
        (
            await db.execute(
                select(sqlfunc.count()).select_from(Visita).where(Visita.tipo == "web_vista")
            )
        ).scalar_one()
        or 0
    )
    if count > 0:
        log.info("Ya hay %d visitas web — saltando demo web/app", count)
        return
    por_urn = await _recursos_por_urn(db)
    recursos_ids = list(por_urn.values())
    datos = generar_visitas_web_app_seed(recursos_ids)
    for d in datos:
        db.add(Visita(**d))
    log.info("Visitas web/app/WiFi/BLE demo creadas: %d", len(datos))


async def seed_demo_contenidos(db: AsyncSession) -> None:
    """Carga contenidos del CMS en distintos estados del flujo editorial."""
    from sqlalchemy import func as sqlfunc

    count = int(
        (await db.execute(select(sqlfunc.count()).select_from(Contenido))).scalar_one() or 0
    )
    if count > 0:
        log.info("Ya hay %d contenidos — saltando demo CMS", count)
        return
    por_urn = await _recursos_por_urn(db)
    recursos_ids = list(por_urn.values())
    datos = generar_contenidos_seed(recursos_ids)
    for d in datos:
        db.add(Contenido(**d))
    log.info("Contenidos CMS demo creados: %d", len(datos))


async def _tabla_vacia(db: AsyncSession, model) -> bool:
    from sqlalchemy import func as sqlfunc

    n = int((await db.execute(select(sqlfunc.count()).select_from(model))).scalar_one() or 0)
    return n == 0


async def seed_verticales(db: AsyncSession) -> None:
    """Carga los activos de las verticales Smart City (idempotente por tabla)."""
    # Alumbrado
    if await _tabla_vacia(db, ZonaAlumbrado):
        for z in ZONAS_ALUMBRADO:
            db.add(
                ZonaAlumbrado(
                    id=z["id"],
                    nombre=z["nombre"],
                    luminarias=z["luminarias"],
                    led=z["led"],
                    vsap=z["vsap"],
                    solar=z["solar"],
                    latitud=z["latitud"],
                    longitud=z["longitud"],
                )
            )
        log.info("Alumbrado · zonas creadas: %d", len(ZONAS_ALUMBRADO))
    if await _tabla_vacia(db, CuadroMando):
        cuadros = generar_cuadros_seed()
        for c in cuadros:
            db.add(CuadroMando(**c))
        log.info("Alumbrado · cuadros de mando creados: %d", len(cuadros))
    if await _tabla_vacia(db, Luminaria):
        lums = generar_luminarias_seed()
        for x in lums:
            db.add(Luminaria(**x))
        log.info("Alumbrado · luminarias creadas: %d", len(lums))
    # Agua
    if await _tabla_vacia(db, SectorAgua):
        secs = generar_sectores_agua_seed()
        for s in secs:
            db.add(SectorAgua(**s))
        log.info("Agua · sectores creados: %d", len(secs))
    # Residuos
    if await _tabla_vacia(db, Contenedor):
        cont = generar_contenedores_seed()
        for c in cont:
            db.add(Contenedor(**c))
        log.info("Residuos · contenedores creados: %d", len(cont))
    # Movilidad
    if await _tabla_vacia(db, PuntoMovilidad):
        pts = generar_movilidad_seed()
        for p in pts:
            db.add(PuntoMovilidad(**p))
        log.info("Movilidad · puntos creados: %d", len(pts))
    # Seguridad
    if await _tabla_vacia(db, CamaraCCTV):
        cams = generar_camaras_seed()
        for c in cams:
            db.add(CamaraCCTV(**c))
        log.info("Seguridad · cámaras creadas: %d", len(cams))
    # Energía
    if await _tabla_vacia(db, SuministroEnergia):
        sums = generar_suministros_energia_seed()
        for s in sums:
            db.add(SuministroEnergia(**s))
        log.info("Energía · suministros (CUPS) creados: %d", len(sums))


async def backfill_coordenadas_verticales(db: AsyncSession) -> None:
    """Rellena coordenadas NULL de filas creadas por seeds antiguos.

    El seed de verticales es idempotente por tabla, así que las bases sembradas
    antes de que los seeds incluyeran latitud/longitud se quedaron sin
    coordenadas (y sus activos no aparecen en el gemelo digital ni en el mapa).
    Solo toca filas con ``latitud IS NULL``: nunca pisa datos reales.
    """
    import hashlib

    zonas = {z["id"]: (z["latitud"], z["longitud"]) for z in ZONAS_ALUMBRADO}

    def dispersion(clave: str, amplitud: float = 0.012) -> tuple[float, float]:
        """Desplazamiento determinista (por clave) alrededor del centro de zona."""
        h = hashlib.sha256(clave.encode()).digest()
        return (
            (h[0] / 255 - 0.5) * 2 * amplitud,
            (h[1] / 255 - 0.5) * 2 * amplitud,
        )

    actualizados = 0

    # Movilidad: coordenadas conocidas por código de punto
    for p in (
        (await db.execute(select(PuntoMovilidad).where(PuntoMovilidad.latitud.is_(None))))
        .scalars()
        .all()
    ):
        if (c := COORDS_MOVILIDAD.get(p.codigo)) is not None:
            p.latitud, p.longitud = c
            actualizados += 1

    # Cámaras: por nombre de emplazamiento; si no, centro de su zona + dispersión.
    # Las que ya tienen coordenadas se reconcilian con el mapa del seed (los
    # emplazamientos son fijos y alguna corrección puntual debe propagarse).
    for cam in (await db.execute(select(CamaraCCTV))).scalars().all():
        c = COORDS_CAMARAS.get(cam.nombre)
        if c is None and cam.latitud is None and cam.zona_id in zonas:
            zlat, zlon = zonas[cam.zona_id]
            dx, dy = dispersion(cam.codigo)
            c = (round(zlat + dx, 6), round(zlon + dy, 6))
        if c is not None and (cam.latitud, cam.longitud) != c:
            cam.latitud, cam.longitud = c
            actualizados += 1

    # Contenedores: centro de su zona + dispersión determinista por código
    for ct in (
        (await db.execute(select(Contenedor).where(Contenedor.latitud.is_(None)))).scalars().all()
    ):
        if ct.zona_id in zonas:
            zlat, zlon = zonas[ct.zona_id]
            dx, dy = dispersion(ct.codigo)
            ct.latitud = round(zlat + dx, 6)
            ct.longitud = round(zlon + dy, 6)
            actualizados += 1

    # Corrección «mar adentro»: en San José y Las Negras el mar está justo al
    # este del núcleo, y la dispersión antigua (±0,012°) dejó activos en el
    # agua. Se reposicionan hacia tierra (oeste del centro de zona) de forma
    # determinista. Solo afecta a filas más allá del umbral de costa.
    reposicionados = 0
    filas_mar: list[Contenedor | CuadroMando] = [
        *(await db.execute(select(Contenedor).where(Contenedor.longitud.is_not(None))))
        .scalars()
        .all(),
        *(await db.execute(select(CuadroMando).where(CuadroMando.longitud.is_not(None))))
        .scalars()
        .all(),
    ]
    for fila in filas_mar:
        umbral = UMBRAL_LON_MAR.get(fila.zona_id)
        if umbral is None or fila.longitud is None or float(fila.longitud) <= umbral:
            continue
        _zlat, zlon = zonas[fila.zona_id]
        dx, _dy = dispersion(fila.codigo)
        fila.longitud = round(zlon - 0.001 - abs(dx), 6)
        reposicionados += 1

    if actualizados or reposicionados:
        log.info(
            "Backfill de coordenadas en verticales: %d rellenadas · %d sacadas del mar",
            actualizados,
            reposicionados,
        )


async def seed_empresas_publicidad(db: AsyncSession) -> None:
    """Empresas anunciantes de demostración para el apartado del tótem."""
    if not await _tabla_vacia(db, EmpresaAnunciante):
        return
    for e in EMPRESAS_SEED:
        db.add(EmpresaAnunciante(**e))
    log.info("Publicidad · empresas demo creadas: %d", len(EMPRESAS_SEED))


async def seed_fuentes_datos(db: AsyncSession) -> None:
    """Carga el catálogo de fuentes de datos e integraciones (idempotente)."""
    if not await _tabla_vacia(db, FuenteDato):
        return
    for f in FUENTES_DATOS_SEED:
        db.add(FuenteDato(**f))
    log.info("Fuentes de datos / integraciones creadas: %d", len(FUENTES_DATOS_SEED))


async def seed_historico_verticales(db: AsyncSession) -> None:
    """Carga 2 años de histórico mensual por vertical (idempotente por tabla)."""
    if not await _tabla_vacia(db, MetricaHistorica):
        return
    filas = generar_historico_seed(anios=2)
    for f in filas:
        db.add(MetricaHistorica(**f))
    log.info("Histórico mensual de verticales creado: %d puntos", len(filas))


async def run() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await seed_roles(db)
            await seed_admin_user(db)
            await seed_cliente(db)
            await seed_recursos(db)
            await seed_sensores(db)
            await seed_faqs(db)
            await db.flush()
            await seed_campanas(db)
            # Demo data (solo si las tablas están vacías)
            await seed_demo_eventos(db)
            await seed_demo_observaciones(db)
            await seed_demo_observaciones_totem(db)
            await seed_demo_opiniones(db)
            await seed_demo_visitas_totem(db)
            await seed_demo_visitas_web_app(db)
            await seed_demo_contenidos(db)
            await seed_demo_chatbot(db)
            await seed_demo_incidencias(db)
            await seed_contexto_backfill(db)
            await seed_verticales(db)
            await backfill_coordenadas_verticales(db)
            await seed_fuentes_datos(db)
            await seed_empresas_publicidad(db)
            await seed_historico_verticales(db)
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
