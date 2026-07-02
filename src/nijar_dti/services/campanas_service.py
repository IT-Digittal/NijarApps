"""Lógica de negocio de las campañas de promoción turística (bloque 9).

Incluye el CRUD mínimo y el cálculo de eficacia (KPIs) cruzando la ventana de
la campaña con las menciones de social listening (``opiniones``) y las visitas
web/app (``visitas``). Para las campañas finalizadas con resultados auditados,
esos valores tienen prioridad sobre el cálculo en vivo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.campana import Campana
from nijar_dti.models.opinion import Opinion, Sentimiento
from nijar_dti.models.visita import TipoVisita, Visita
from nijar_dti.schemas.campanas import CampanaIn, CampanaKPIs, CampanaUpdate


class NotFound(Exception):
    pass


async def listar_campanas(
    db: AsyncSession,
    estado: str | None = None,
) -> list[Campana]:
    q = select(Campana).where(Campana.deleted_at.is_(None))
    if estado:
        q = q.where(Campana.estado == estado)
    q = q.order_by(Campana.fecha_inicio.desc())
    return list((await db.execute(q)).scalars().all())


async def obtener_campana(db: AsyncSession, campana_id: UUID) -> Campana:
    res = await db.execute(
        select(Campana).where(Campana.id == campana_id, Campana.deleted_at.is_(None))
    )
    campana = res.scalar_one_or_none()
    if campana is None:
        raise NotFound("Campaña no encontrada")
    return campana


async def crear_campana(db: AsyncSession, payload: CampanaIn) -> Campana:
    campana = Campana(**payload.model_dump())
    db.add(campana)
    await db.flush()
    # Refrescar valores server-side (created_at/updated_at) antes de serializar.
    await db.refresh(campana)
    return campana


async def actualizar_campana(
    db: AsyncSession, campana_id: UUID, payload: CampanaUpdate
) -> Campana:
    campana = await obtener_campana(db, campana_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(campana, campo, valor)
    await db.flush()
    await db.refresh(campana)
    return campana


async def eliminar_campana(db: AsyncSession, campana_id: UUID) -> None:
    campana = await obtener_campana(db, campana_id)
    campana.deleted_at = datetime.now(timezone.utc)
    await db.flush()


def _pct(numerador: float, denominador: float) -> float | None:
    if denominador <= 0:
        return None
    return round(numerador / denominador * 100, 1)


async def _contar_visitas(
    db: AsyncSession, tipo: TipoVisita, desde: datetime, hasta: datetime
) -> int:
    q = (
        select(func.count())
        .select_from(Visita)
        .where(Visita.tipo == tipo, Visita.ocurrido_en >= desde, Visita.ocurrido_en < hasta)
    )
    return int((await db.execute(q)).scalar_one() or 0)


async def calcular_kpis(db: AsyncSession, campana: Campana) -> CampanaKPIs:
    """Calcula la eficacia de la campaña cruzando menciones y visitas.

    Los resultados auditados almacenados en ``campana.resultados`` tienen
    prioridad sobre el cálculo en vivo (campañas finalizadas).
    """
    inicio = campana.fecha_inicio
    fin = campana.fecha_fin
    duracion = fin - inicio

    # ---- Menciones dentro de la ventana ----
    op_ventana = list(
        (
            await db.execute(
                select(Opinion).where(
                    Opinion.publicado_en >= inicio, Opinion.publicado_en <= fin
                )
            )
        )
        .scalars()
        .all()
    )
    # Preferir las menciones etiquetadas con la campaña; si no hay, usar todas.
    etiquetadas = [
        o for o in op_ventana if (o.metricas or {}).get("campana") == campana.slug
    ]
    base = etiquetadas if (campana.slug and etiquetadas) else op_ventana

    menciones = len(base)
    positivas = sum(1 for o in base if o.sentimiento == Sentimiento.POSITIVO)
    negativas = sum(1 for o in base if o.sentimiento == Sentimiento.NEGATIVO)
    alcance = sum(int((o.metricas or {}).get("alcance_estimado", 0) or 0) for o in base)
    interacciones = sum(
        int((o.metricas or {}).get("likes", 0) or 0)
        + int((o.metricas or {}).get("comentarios", 0) or 0)
        + int((o.metricas or {}).get("compartidos", 0) or 0)
        for o in base
    )

    # ---- Visitas web/app dentro de la ventana ----
    visitas_web = await _contar_visitas(db, TipoVisita.WEB_VISTA, inicio, fin)
    visitas_app = await _contar_visitas(db, TipoVisita.APP_VISTA, inicio, fin)

    # ---- Comparativa con el periodo anterior de igual duración ----
    prev_inicio = inicio - duracion
    op_prev = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Opinion)
                .where(Opinion.publicado_en >= prev_inicio, Opinion.publicado_en < inicio)
            )
        ).scalar_one()
        or 0
    )
    visitas_web_prev = await _contar_visitas(db, TipoVisita.WEB_VISTA, prev_inicio, inicio)
    visitas_app_prev = await _contar_visitas(db, TipoVisita.APP_VISTA, prev_inicio, inicio)
    visitas_prev = visitas_web_prev + visitas_app_prev
    visitas_total = visitas_web + visitas_app

    incremento_menciones = (
        _pct(menciones - op_prev, op_prev) if op_prev else None
    )
    incremento_visitas = (
        _pct(visitas_total - visitas_prev, visitas_prev) if visitas_prev else None
    )

    kpis = CampanaKPIs(
        campana_id=campana.id,
        slug=campana.slug,
        nombre=campana.nombre,
        estado=campana.estado,
        fecha_inicio=inicio,
        fecha_fin=fin,
        menciones=menciones,
        menciones_positivas=positivas,
        menciones_negativas=negativas,
        sentimiento_positivo_pct=_pct(positivas, menciones),
        alcance_estimado=alcance,
        interacciones=interacciones,
        visitas_web=visitas_web,
        visitas_app=visitas_app,
        menciones_periodo_anterior=op_prev,
        incremento_menciones_pct=incremento_menciones,
        visitas_periodo_anterior=visitas_prev,
        incremento_visitas_pct=incremento_visitas,
    )

    # ---- Prioridad a los resultados auditados (campañas finalizadas) ----
    r = campana.resultados or {}
    if r:
        if "menciones" in r:
            kpis.menciones = int(r["menciones"])
        if "visitas_web" in r:
            kpis.visitas_web = int(r["visitas_web"])
        if "alcance" in r:
            kpis.alcance_estimado = int(r["alcance"])
        if "interacciones" in r:
            kpis.interacciones = int(r["interacciones"])
        if "sentimiento_positivo_pct" in r:
            kpis.sentimiento_positivo_pct = float(r["sentimiento_positivo_pct"])
        if "incremento_menciones_pct" in r:
            kpis.incremento_menciones_pct = float(r["incremento_menciones_pct"])
        if "incremento_visitas_pct" in r:
            kpis.incremento_visitas_pct = float(r["incremento_visitas_pct"])

    return kpis
