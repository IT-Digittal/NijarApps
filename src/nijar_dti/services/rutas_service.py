"""Planificador de rutas y motor de recomendaciones (A.1 / B.2).

- ``planificar_ruta``: propone un itinerario encadenado de recursos turísticos
  publicados, ordenado por cercanía desde un punto de origen (típicamente el
  propio tótem) y filtrable por categorías.
- ``recomendaciones``: propone visitas (recursos) y asistencia a eventos
  próximos, base de la función "proponer visitas y eventos" del asistente.

La geometría se resuelve con las utilidades puras de ``core/geo.py``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.geo import (
    Parada,
    distancia_total_m,
    duracion_estimada_min,
    haversine_m,
    ordenar_itinerario,
)
from nijar_dti.models.evento_turistico import EventoTuristico
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.schemas.rutas import (
    EventoSugerido,
    ParadaOut,
    PlanificarRutaIn,
    RecomendacionesOut,
    RecursoSugerido,
    RutaPlanificada,
)


def _nombre_idioma(nombre: str, nombre_i18n: dict | None, idioma: str) -> str:
    if nombre_i18n and isinstance(nombre_i18n, dict) and nombre_i18n.get(idioma):
        return str(nombre_i18n[idioma])
    return nombre


async def _recursos_publicados_con_coords(
    db: AsyncSession, categorias: list[str] | None
) -> list[tuple]:
    q = select(
        RecursoTuristico.id,
        RecursoTuristico.nombre,
        RecursoTuristico.categoria,
        RecursoTuristico.nombre_i18n,
        func.ST_AsGeoJSON(RecursoTuristico.ubicacion).label("geojson"),
    ).where(
        RecursoTuristico.publicado.is_(True),
        RecursoTuristico.activo.is_(True),
        RecursoTuristico.deleted_at.is_(None),
        RecursoTuristico.ubicacion.is_not(None),
    )
    if categorias:
        q = q.where(RecursoTuristico.categoria.in_(categorias))
    return list((await db.execute(q)).all())  # type: ignore[arg-type]


def _parsea_coords(geojson: str | None) -> tuple[float, float] | None:
    if not geojson:
        return None
    try:
        data = json.loads(geojson)
        lon, lat = data["coordinates"][0], data["coordinates"][1]
        return float(lat), float(lon)
    except (ValueError, KeyError, TypeError, IndexError):
        return None


async def planificar_ruta(db: AsyncSession, payload: PlanificarRutaIn) -> RutaPlanificada:
    filas = await _recursos_publicados_con_coords(db, payload.categorias)

    paradas: list[Parada] = []
    meta: dict[str, tuple] = {}
    for fila in filas:
        coords = _parsea_coords(fila.geojson)  # type: ignore[attr-defined]
        if coords is None:
            continue
        lat, lon = coords
        paradas.append(
            Parada(
                id=str(fila.id),  # type: ignore[attr-defined]
                nombre=fila.nombre,  # type: ignore[attr-defined]
                categoria=str(fila.categoria),  # type: ignore[attr-defined]
                lat=lat,
                lon=lon,
            )
        )
        meta[str(fila.id)] = (fila.nombre, fila.nombre_i18n, str(fila.categoria))  # type: ignore[attr-defined]

    ruta = ordenar_itinerario(payload.lat, payload.lon, paradas, payload.max_paradas)

    paradas_out: list[ParadaOut] = []
    lat_prev, lon_prev = payload.lat, payload.lon
    acumulada = 0.0
    for i, p in enumerate(ruta, start=1):
        d = round(haversine_m(lat_prev, lon_prev, p.lat, p.lon), 1)
        acumulada = round(acumulada + d, 1)
        nombre, nombre_i18n, categoria = meta[p.id]
        paradas_out.append(
            ParadaOut(
                orden=i,
                id=p.id,
                nombre=_nombre_idioma(nombre, nombre_i18n, payload.idioma),
                categoria=categoria,
                lat=p.lat,
                lon=p.lon,
                distancia_desde_anterior_m=d,
                distancia_acumulada_m=acumulada,
            )
        )
        lat_prev, lon_prev = p.lat, p.lon

    total = distancia_total_m(payload.lat, payload.lon, ruta)
    mensaje = None
    if not paradas_out:
        mensaje = "No hay recursos publicados con ubicación para los criterios indicados."

    return RutaPlanificada(
        origen={"lat": payload.lat, "lon": payload.lon},
        modo=payload.modo,
        paradas=paradas_out,
        distancia_total_m=total,
        duracion_desplazamiento_min=duracion_estimada_min(total, payload.modo),
        mensaje=mensaje,
    )


async def recomendaciones(
    db: AsyncSession,
    idioma: str = "es",
    dias: int = 30,
    limite: int = 6,
) -> RecomendacionesOut:
    ahora = datetime.now(UTC)
    hasta = ahora + timedelta(days=dias)

    # Eventos próximos publicados
    q_ev = (
        select(EventoTuristico)
        .where(
            EventoTuristico.publicado.is_(True),
            EventoTuristico.activo.is_(True),
            EventoTuristico.deleted_at.is_(None),
            EventoTuristico.fecha_fin >= ahora,
            EventoTuristico.fecha_inicio <= hasta,
        )
        .order_by(EventoTuristico.fecha_inicio)
        .limit(limite)
    )
    eventos = list((await db.execute(q_ev)).scalars().all())
    eventos_out = [
        EventoSugerido(
            id=e.id,
            nombre=_nombre_idioma(e.nombre, e.nombre_i18n, idioma),
            tipo=str(e.tipo),
            fecha_inicio=e.fecha_inicio,
            fecha_fin=e.fecha_fin,
            direccion=e.direccion,
        )
        for e in eventos
    ]

    # Recursos sugeridos (publicados); prioriza variedad de categorías
    q_rec = (
        select(RecursoTuristico)
        .where(
            RecursoTuristico.publicado.is_(True),
            RecursoTuristico.activo.is_(True),
            RecursoTuristico.deleted_at.is_(None),
        )
        .limit(limite * 3)
    )
    recursos = list((await db.execute(q_rec)).scalars().all())
    vistos: set[str] = set()
    recursos_out: list[RecursoSugerido] = []
    for r in recursos:
        cat = str(r.categoria)
        motivo = "Variedad de la oferta del destino" if cat not in vistos else "Recurso destacado"
        vistos.add(cat)
        recursos_out.append(
            RecursoSugerido(
                id=r.id,
                nombre=_nombre_idioma(r.nombre, r.nombre_i18n, idioma),
                categoria=cat,
                motivo=motivo,
            )
        )
        if len(recursos_out) >= limite:
            break

    mensaje = None
    if not eventos_out and not recursos_out:
        mensaje = "No hay eventos ni recursos publicados disponibles por ahora."

    return RecomendacionesOut(
        fecha_referencia=ahora,
        idioma=idioma,
        eventos=eventos_out,
        recursos=recursos_out,
        mensaje=mensaje,
    )
