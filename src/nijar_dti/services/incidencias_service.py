"""Lógica de negocio del ticketing de incidencias (C.1).

Provee el CRUD mínimo y las agregaciones que alimentan el informe mensual
de servicio: disponibilidad por componente (a partir del tiempo de
indisponibilidad real), recuento por severidad y cumplimiento ANS.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.ans import (
    SLA_DISPONIBILIDAD_PORC,
    disponibilidad_porcentaje,
    evalua_ans,
    horas_entre,
)
from nijar_dti.models.incidencia import EstadoIncidencia, Incidencia
from nijar_dti.schemas.incidencias import (
    CumplimientoANSSeveridad,
    IncidenciaIn,
    IncidenciaResolverIn,
    InformeANS,
)

# Componentes cuyo informe de disponibilidad se reporta siempre (100 % si no
# hay indisponibilidad registrada en el periodo).
COMPONENTES_DISPONIBILIDAD = (
    "plataforma",
    "totem_1",
    "totem_2",
    "chatbot",
    "smart_office",
    "big_data",
)


class NotFound(Exception):
    pass


async def crear_incidencia(db: AsyncSession, payload: IncidenciaIn) -> Incidencia:
    inc = Incidencia(
        severidad=payload.severidad,
        titulo=payload.titulo,
        componente=payload.componente,
        detectada_en=payload.detectada_en or datetime.now(UTC),
        descripcion=payload.descripcion,
        origen=payload.origen,
        afecta_disponibilidad=payload.afecta_disponibilidad,
        es_preventiva=payload.es_preventiva,
        es_evento_seguridad=payload.es_evento_seguridad,
    )
    db.add(inc)
    await db.flush()
    return inc


async def listar_incidencias(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    estado: str | None = None,
    severidad: str | None = None,
) -> list[Incidencia]:
    q = select(Incidencia)
    if desde:
        q = q.where(Incidencia.detectada_en >= desde)
    if hasta:
        q = q.where(Incidencia.detectada_en <= hasta)
    if estado:
        q = q.where(Incidencia.estado == estado)
    if severidad:
        q = q.where(Incidencia.severidad == severidad)
    q = q.order_by(Incidencia.detectada_en.desc())
    return list((await db.execute(q)).scalars().all())


async def resolver_incidencia(
    db: AsyncSession, incidencia_id, payload: IncidenciaResolverIn
) -> Incidencia:
    inc = await db.get(Incidencia, incidencia_id)
    if inc is None:
        raise NotFound(f"Incidencia {incidencia_id} no encontrada")
    ahora = datetime.now(UTC)
    if payload.respondida_en is not None or inc.respondida_en is None:
        inc.respondida_en = payload.respondida_en or inc.respondida_en or ahora
    inc.resuelta_en = payload.resuelta_en or ahora
    if payload.incidente_confirmado is not None:
        inc.incidente_confirmado = payload.incidente_confirmado
    inc.estado = EstadoIncidencia.RESUELTA
    await db.flush()
    return inc


async def _incidencias_periodo(
    db: AsyncSession, inicio: datetime, fin: datetime
) -> list[Incidencia]:
    q = (
        select(Incidencia)
        .where(Incidencia.detectada_en >= inicio)
        .where(Incidencia.detectada_en < fin)
    )
    return list((await db.execute(q)).scalars().all())


def calcular_disponibilidad(
    incidencias: list[Incidencia], inicio: datetime, fin: datetime
) -> dict[str, float]:
    """Disponibilidad por componente a partir del downtime real registrado."""
    periodo_min = (fin - inicio).total_seconds() / 60
    downtime: dict[str, float] = dict.fromkeys(COMPONENTES_DISPONIBILIDAD, 0.0)
    for inc in incidencias:
        if not inc.afecta_disponibilidad or inc.resuelta_en is None:
            continue
        minutos = (inc.resuelta_en - inc.detectada_en).total_seconds() / 60
        downtime[inc.componente] = downtime.get(inc.componente, 0.0) + max(minutos, 0.0)
    return {comp: disponibilidad_porcentaje(mins, periodo_min) for comp, mins in downtime.items()}


def resumen_incidencias(incidencias: list[Incidencia]) -> dict[str, int]:
    """Recuentos que alimentan el informe mensual."""
    reactivas = [i for i in incidencias if not i.es_preventiva]
    return {
        "criticas": sum(1 for i in reactivas if i.severidad == "critica"),
        "altas": sum(1 for i in reactivas if i.severidad == "alta"),
        "resueltas": sum(1 for i in reactivas if i.resuelta_en is not None),
        "eventos_seguridad": sum(1 for i in incidencias if i.es_evento_seguridad),
        "incidentes_confirmados": sum(1 for i in incidencias if i.incidente_confirmado),
        "preventivas": sum(1 for i in incidencias if i.es_preventiva),
    }


def agregar_cumplimiento_ans(incidencias: list, inicio: datetime, fin: datetime) -> InformeANS:
    """Agrega el cumplimiento ANS de una lista de incidencias (función pura)."""
    reactivas = [i for i in incidencias if not i.es_preventiva]
    por_sev: list[CumplimientoANSSeveridad] = []
    for sev in ("critica", "alta", "media", "baja"):
        grupo = [i for i in reactivas if i.severidad == sev]
        if not grupo:
            por_sev.append(CumplimientoANSSeveridad(severidad=sev))
            continue
        evals = [evalua_ans(sev, i.detectada_en, i.respondida_en, i.resuelta_en) for i in grupo]
        resueltas = [e for e in evals if e.cumple_resolucion is not None]
        cumplen = sum(1 for e in resueltas if e.cumple_resolucion)
        resp = [e.respuesta_h for e in evals if e.respuesta_h is not None]
        reso = [e.resolucion_h for e in evals if e.resolucion_h is not None]
        por_sev.append(
            CumplimientoANSSeveridad(
                severidad=sev,
                total=len(grupo),
                cumplen_resolucion=cumplen,
                porcentaje_cumplimiento=(
                    round(cumplen * 100 / len(resueltas), 1) if resueltas else None
                ),
                tiempo_medio_respuesta_h=round(sum(resp) / len(resp), 2) if resp else None,
                tiempo_medio_resolucion_h=round(sum(reso) / len(reso), 2) if reso else None,
            )
        )
    return InformeANS(
        desde=inicio,
        hasta=fin,
        por_severidad=por_sev,
        incidencias_totales=len(reactivas),
        sla_disponibilidad_porc=SLA_DISPONIBILIDAD_PORC,
    )


async def informe_ans(db: AsyncSession, inicio: datetime, fin: datetime) -> InformeANS:
    incidencias = await _incidencias_periodo(db, inicio, fin)
    return agregar_cumplimiento_ans(incidencias, inicio, fin)


def tiempo_medio_resolucion_h(incidencias: list[Incidencia]) -> float | None:
    horas = [
        horas_entre(i.detectada_en, i.resuelta_en)
        for i in incidencias
        if i.resuelta_en is not None and not i.es_preventiva
    ]
    horas = [h for h in horas if h is not None]
    return round(sum(horas) / len(horas), 2) if horas else None
