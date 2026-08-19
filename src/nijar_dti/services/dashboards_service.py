"""Lógica de negocio de dashboards (Smart Office, Big Data, informe mensual)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.faq import InteraccionChatbot
from nijar_dti.models.observacion import Observacion
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.sensor import Sensor
from nijar_dti.models.visita import TipoVisita, Visita
from nijar_dti.schemas.common import PuntoSerieDiaria, SerieDiaria
from nijar_dti.schemas.dashboards import (
    BigDataOverview,
    EnvironmentPoint,
    EnvironmentSeries,
    MonthlyReport,
    SmartOfficeOverview,
    TotemHealth,
    TotemsHealthOverview,
    TotemUsageStats,
)

# -------------------------- Smart Office --------------------------

_TIPOS_AMBIENTAL = {
    "ambiental_co2": "co2_actual_ppm",
    "ambiental_temperatura": "temperatura_actual_c",
    "ambiental_humedad": "humedad_actual_porc",
    "ambiental_ruido": "ruido_actual_db",
}


async def smart_office_overview(db: AsyncSession) -> SmartOfficeOverview:
    sensores = (await db.execute(select(Sensor).where(Sensor.deleted_at.is_(None)))).scalars().all()
    sensores_total = len(sensores)
    sensores_operativos = sum(1 for s in sensores if s.estado == "operativo")
    sensores_offline = sum(1 for s in sensores if s.estado in {"offline", "averia", "desconocido"})

    # última observación de cada tipo ambiental
    overview: dict[str, float | None] = dict.fromkeys(_TIPOS_AMBIENTAL.values())
    for tipo, campo in _TIPOS_AMBIENTAL.items():
        sensor_ids = [s.id for s in sensores if s.tipo == tipo and s.activo]
        if not sensor_ids:
            continue
        q = (
            select(Observacion.valor)
            .where(Observacion.sensor_id.in_(sensor_ids))
            .where(Observacion.valido.is_(True))
            .order_by(Observacion.observado_en.desc())
            .limit(1)
        )
        res = await db.execute(q)
        valor = res.scalar_one_or_none()
        if valor is not None:
            overview[campo] = float(valor)

    # alertas activas: observaciones por encima/debajo de umbrales en última hora
    alertas = 0
    una_hora_atras = datetime.now(UTC) - timedelta(hours=1)
    for s in sensores:
        if not s.umbrales_alerta:
            continue
        umbral_max = s.umbrales_alerta.get("critical_max") or s.umbrales_alerta.get("warning_max")
        if umbral_max is None:
            continue
        q = (
            select(func.count())  # type: ignore[assignment]
            .select_from(Observacion)
            .where(
                Observacion.sensor_id == s.id,
                Observacion.observado_en >= una_hora_atras,
                Observacion.valor > umbral_max,
            )
        )
        n = int((await db.execute(q)).scalar_one() or 0)
        alertas += n

    return SmartOfficeOverview(
        sensores_total=sensores_total,
        sensores_operativos=sensores_operativos,
        sensores_offline=sensores_offline,
        alertas_activas=alertas,
        co2_actual_ppm=overview["co2_actual_ppm"],
        temperatura_actual_c=overview["temperatura_actual_c"],
        humedad_actual_porc=overview["humedad_actual_porc"],
        ruido_actual_db=overview["ruido_actual_db"],
        timestamp=datetime.now(UTC),
    )


_GRANULARIDAD_MAP = {
    "minuto": "minute",
    "hora": "hour",
    "dia": "day",
}


async def environment_series(
    db: AsyncSession,
    desde: datetime | None,
    hasta: datetime | None,
    granularidad: str = "hora",
) -> EnvironmentSeries:
    pg_unit = _GRANULARIDAD_MAP.get(granularidad, "hour")
    bucket = func.date_trunc(pg_unit, Observacion.observado_en).label("bucket")

    q = (
        select(
            bucket,
            Sensor.tipo,
            func.avg(Observacion.valor).label("media"),
        )
        .join(Sensor, Sensor.id == Observacion.sensor_id)
        .where(
            Observacion.valido.is_(True),
            Sensor.tipo.in_(list(_TIPOS_AMBIENTAL.keys())),
        )
    )
    if desde:
        q = q.where(Observacion.observado_en >= desde)
    if hasta:
        q = q.where(Observacion.observado_en <= hasta)
    q = q.group_by(bucket, Sensor.tipo).order_by(bucket)

    rows = (await db.execute(q)).all()

    # agrupa por timestamp para construir EnvironmentPoint completos
    por_bucket: dict[datetime, EnvironmentPoint] = {}
    for row in rows:
        ts = row.bucket
        if ts not in por_bucket:
            por_bucket[ts] = EnvironmentPoint(timestamp=ts)
        media = float(row.media) if row.media is not None else None
        if row.tipo == "ambiental_co2":
            por_bucket[ts].co2_ppm = media
        elif row.tipo == "ambiental_temperatura":
            por_bucket[ts].temperatura_c = media
        elif row.tipo == "ambiental_humedad":
            por_bucket[ts].humedad_porc = media
        elif row.tipo == "ambiental_ruido":
            por_bucket[ts].ruido_db = media

    puntos = sorted(por_bucket.values(), key=lambda p: p.timestamp)
    return EnvironmentSeries(granularidad=granularidad, desde=desde, hasta=hasta, puntos=puntos)


# -------------------------- Big Data --------------------------


async def big_data_overview(db: AsyncSession) -> BigDataOverview:
    total = int((await db.execute(select(func.count()).select_from(Opinion))).scalar_one() or 0)

    hace_un_mes = datetime.now(UTC) - timedelta(days=30)
    ultimo_mes = int(
        (
            await db.execute(
                select(func.count()).select_from(Opinion).where(Opinion.publicado_en >= hace_un_mes)
            )
        ).scalar_one()
        or 0
    )

    sentimiento_medio_res = await db.execute(
        select(func.avg(Opinion.score_sentimiento)).where(Opinion.score_sentimiento.is_not(None))
    )
    sentimiento_medio = sentimiento_medio_res.scalar_one_or_none()

    fuentes = (await db.execute(select(Opinion.fuente).distinct())).scalars().all()

    # top 5 temas
    temas_rows = (await db.execute(select(Opinion.temas).where(Opinion.temas.is_not(None)))).all()
    contador: Counter[str] = Counter()
    for r in temas_rows:
        if r[0]:
            contador.update(r[0])
    temas_top = [t for t, _ in contador.most_common(5)]

    return BigDataOverview(
        menciones_total=total,
        menciones_ultimo_mes=ultimo_mes,
        sentimiento_medio=float(sentimiento_medio) if sentimiento_medio is not None else None,
        fuentes_activas=len(fuentes),
        temas_top=temas_top,
    )


# -------------------------- Tótems --------------------------


async def totems_usage(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> TotemUsageStats:
    base = select(Visita).where(Visita.tipo == TipoVisita.INTERACCION_TOTEM)
    if desde:
        base = base.where(Visita.ocurrido_en >= desde)
    if hasta:
        base = base.where(Visita.ocurrido_en <= hasta)
    interacciones = list((await db.execute(base)).scalars().all())

    total = len(interacciones)
    visitantes = {v.visitante_hash for v in interacciones if v.visitante_hash}

    duraciones = [
        v.atributos.get("duracion_seg")
        for v in interacciones
        if v.atributos and isinstance(v.atributos.get("duracion_seg"), (int, float))
    ]
    duracion_media = round(sum(duraciones) / len(duraciones), 2) if duraciones else None  # type: ignore[arg-type]

    secciones: Counter[str] = Counter()
    for v in interacciones:
        if v.atributos:
            seccion = v.atributos.get("seccion")
            if seccion:
                secciones[seccion] += 1
    top_secciones = [{"seccion": s, "interacciones": n} for s, n in secciones.most_common(10)]

    return TotemUsageStats(
        desde=desde,
        hasta=hasta,
        interacciones_total=total,
        sesiones_unicas=len(visitantes),
        duracion_media_seg=duracion_media,
        secciones_top=top_secciones,
    )


async def totems_usage_series(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> SerieDiaria:
    """Serie temporal diaria de interacciones registradas en los tótems.

    Cuenta las visitas de tipo ``interaccion_totem`` agrupadas por día de
    ocurrencia para la gráfica de uso del dashboard.
    """
    bucket = func.date_trunc("day", Visita.ocurrido_en).label("bucket")
    q = select(bucket, func.count().label("total")).where(
        Visita.tipo == TipoVisita.INTERACCION_TOTEM
    )
    if desde:
        q = q.where(Visita.ocurrido_en >= desde)
    if hasta:
        q = q.where(Visita.ocurrido_en <= hasta)
    q = q.group_by(bucket).order_by(bucket)

    rows = (await db.execute(q)).all()
    puntos = [PuntoSerieDiaria(fecha=row.bucket.date(), total=int(row.total)) for row in rows]
    return SerieDiaria(desde=desde, hasta=hasta, puntos=puntos)


async def totems_health(db: AsyncSession) -> TotemsHealthOverview:
    """Disponibilidad y telemetría por tótem (bloque 7 del pliego).

    Calcula, por cada sensor de tipo ``totem``, la disponibilidad (muestras
    online / muestras totales), la temperatura interna media/máxima, los
    reinicios y la conectividad media a partir de sus observaciones.
    """
    sensores = list(
        (
            await db.execute(
                select(Sensor).where(Sensor.tipo == "totem", Sensor.deleted_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    totems: list[TotemHealth] = []
    disponibilidades: list[float] = []
    for s in sensores:
        obs = list(
            (
                await db.execute(
                    select(Observacion)
                    .where(Observacion.sensor_id == s.id)
                    .order_by(Observacion.observado_en)
                )
            )
            .scalars()
            .all()
        )
        muestras = len(obs)
        online = 0
        temps: list[float] = []
        conect: list[float] = []
        reinicios = 0
        ultima_com: datetime | None = None
        for o in obs:
            valores = o.valores or {}
            if valores.get("online") == 1:
                online += 1
            t = valores.get("temperatura_interna")
            if isinstance(t, (int, float)):
                temps.append(float(t))
            c = valores.get("conectividad_pct")
            if isinstance(c, (int, float)):
                conect.append(float(c))
            reinicios = max(reinicios, int(valores.get("reinicios_acumulados", 0) or 0))
            ultima_com = o.observado_en
        disponibilidad = round(online / muestras * 100, 2) if muestras else None
        if disponibilidad is not None:
            disponibilidades.append(disponibilidad)
        totems.append(
            TotemHealth(
                urn=s.urn,
                nombre=s.nombre,
                estado=s.estado,
                disponibilidad_pct=disponibilidad,
                temperatura_interna_media=round(sum(temps) / len(temps), 1) if temps else None,
                temperatura_interna_max=round(max(temps), 1) if temps else None,
                reinicios=reinicios,
                conectividad_media_pct=round(sum(conect) / len(conect), 1) if conect else None,
                ultima_comunicacion=ultima_com,
                muestras=muestras,
            )
        )
    media = round(sum(disponibilidades) / len(disponibilidades), 2) if disponibilidades else None
    return TotemsHealthOverview(disponibilidad_media_pct=media, totems=totems)


# -------------------------- Informe mensual (C.1) --------------------------


async def informe_mensual(db: AsyncSession, year: int, month: int) -> MonthlyReport:
    inicio = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        fin = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        fin = datetime(year, month + 1, 1, tzinfo=UTC)

    interacciones_totems = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Visita)
                .where(Visita.tipo == TipoVisita.INTERACCION_TOTEM)
                .where(Visita.ocurrido_en >= inicio)
                .where(Visita.ocurrido_en < fin)
            )
        ).scalar_one()
        or 0
    )

    sesiones_chatbot = int(
        (
            await db.execute(
                select(func.count(func.distinct(InteraccionChatbot.sesion_id)))
                .where(InteraccionChatbot.created_at >= inicio)
                .where(InteraccionChatbot.created_at < fin)
            )
        ).scalar_one()
        or 0
    )

    visitas_web = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Visita)
                .where(Visita.tipo == TipoVisita.WEB_VISTA)
                .where(Visita.ocurrido_en >= inicio)
                .where(Visita.ocurrido_en < fin)
            )
        ).scalar_one()
        or 0
    )

    # Incidencias reales del periodo (ticketing C.1) — disponibilidad y recuentos
    from nijar_dti.services import incidencias_service as inc_svc

    incidencias_periodo = await inc_svc._incidencias_periodo(db, inicio, fin)
    disponibilidad = inc_svc.calcular_disponibilidad(incidencias_periodo, inicio, fin)
    resumen = inc_svc.resumen_incidencias(incidencias_periodo)

    # Eficacia digital — GA4 (con fallback a datos sintéticos en dry-run)
    eficacia_digital = await _ga4_overview_seguro()

    menciones = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Opinion)
                .where(Opinion.publicado_en >= inicio)
                .where(Opinion.publicado_en < fin)
            )
        ).scalar_one()
        or 0
    )

    sent_medio_val = (
        await db.execute(
            select(func.avg(Opinion.score_sentimiento))
            .where(Opinion.publicado_en >= inicio)
            .where(Opinion.publicado_en < fin)
            .where(Opinion.score_sentimiento.is_not(None))
        )
    ).scalar_one_or_none()

    return MonthlyReport(
        year=year,
        month=month,
        disponibilidad_por_componente=disponibilidad,
        interacciones_totems=interacciones_totems,
        sesiones_chatbot=sesiones_chatbot,
        visitas_web_estimadas=visitas_web,
        incidencias_criticas=resumen["criticas"],
        incidencias_altas=resumen["altas"],
        incidencias_resueltas=resumen["resueltas"],
        eventos_seguridad=resumen["eventos_seguridad"],
        incidentes_confirmados=resumen["incidentes_confirmados"],
        acciones_preventivas_ejecutadas=resumen["preventivas"],
        sentimiento_medio=float(sent_medio_val) if sent_medio_val is not None else None,
        menciones_periodo=menciones,
        eficacia_digital=eficacia_digital,
    )


async def _ga4_overview_seguro() -> dict | None:
    """Llama a GA4 protegiendo el informe ante errores transitorios.

    Si las credenciales no están o GA4 falla, devuelve None para que el
    informe se entregue de todas formas. La causa real queda en el log.
    """
    try:
        from nijar_dti.connectors.analytics.ga4 import GA4Connector

        connector = GA4Connector()
        ov = await connector.overview(days_back=30)
        channels = await connector.channels_breakdown(days_back=30)
        return {
            "configurado": connector.is_configured,
            "sesiones_30d": ov.sesiones,
            "usuarios_30d": ov.usuarios,
            "usuarios_nuevos_30d": ov.usuarios_nuevos,
            "paginas_vistas_30d": ov.paginas_vistas,
            "duracion_media_sesion_seg": ov.duracion_media_sesion_seg,
            "bounce_rate": ov.bounce_rate,
            "canales": [
                {"canal": c.canal, "sesiones": c.sesiones, "usuarios": c.usuarios} for c in channels
            ],
        }
    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning("GA4 no disponible: %s", exc)
        return None
