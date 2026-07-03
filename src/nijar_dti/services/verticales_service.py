"""Lógica de negocio de las verticales Smart City.

Calcula los KPIs de cada vertical (alumbrado, agua, residuos, movilidad,
seguridad y energía) a partir de los activos persistidos, y ofrece los
listados (con paginación en los de alta cardinalidad).
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.alumbrado import CuadroMando, Luminaria, ZonaAlumbrado
from nijar_dti.models.verticales import (
    CamaraCCTV,
    Contenedor,
    PuntoMovilidad,
    SectorAgua,
    SuministroEnergia,
)
from nijar_dti.schemas.verticales import (
    AguaOverview,
    AlumbradoOverview,
    CamaraCCTVOut,
    ContenedoresPage,
    ContenedorOut,
    CuadroMandoOut,
    EnergiaOverview,
    LuminariaOut,
    LuminariasPage,
    MovilidadOverview,
    PuntoMovilidadOut,
    ResiduosOverview,
    SectorAguaOut,
    SeguridadOverview,
    SuministroEnergiaOut,
    SuministrosPage,
    ZonaAlumbradoOut,
)


def _pct(num: float, den: float) -> float:
    return round(num / den * 100, 1) if den else 0.0


async def _all(db: AsyncSession, model):
    return list((await db.execute(select(model))).scalars().all())


# ----------------------------------------------------------------- ALUMBRADO
async def alumbrado_overview(db: AsyncSession) -> AlumbradoOverview:
    zonas = sorted(await _all(db, ZonaAlumbrado), key=lambda z: -z.luminarias)
    cuadros = await _all(db, CuadroMando)
    lums = await _all(db, Luminaria)

    total = len(lums)
    led = sum(1 for x in lums if x.tecnologia == "led")
    vsap = sum(1 for x in lums if x.tecnologia == "vsap")
    solar = sum(1 for x in lums if x.tecnologia == "solar")
    operativas = sum(1 for x in lums if x.estado == "operativo")
    averia = sum(1 for x in lums if x.estado == "averia")
    sincom = sum(1 for x in lums if x.estado == "sin_comunicacion")
    consumo = float(sum(float(x.consumo_mes_kwh or 0) for x in lums))
    potencia = round(sum(x.potencia_w for x in lums) / 1000, 1)

    cuadros_online = sum(1 for c in cuadros if c.estado == "operativo")
    cuadros_alerta = sum(1 for c in cuadros if c.estado in ("alerta", "sin_comunicacion"))
    circuitos = sum(c.circuitos for c in cuadros)
    incidencias = sum(1 for c in cuadros if c.alarmas) + averia + sincom

    return AlumbradoOverview(
        total_luminarias=total, led=led, vsap=vsap, solar=solar, pct_led=_pct(led, total),
        operativas=operativas, en_averia=averia, sin_comunicacion=sincom,
        disponibilidad_pct=_pct(operativas, total),
        cuadros_total=len(cuadros), cuadros_online=cuadros_online, cuadros_alerta=cuadros_alerta,
        circuitos_total=circuitos, potencia_instalada_kw=potencia,
        consumo_mes_kwh=round(consumo, 1), ahorro_energetico_pct=31.0,
        incidencias_abiertas=incidencias,
        zonas=[ZonaAlumbradoOut.model_validate(z) for z in zonas],
    )


async def alumbrado_zonas(db: AsyncSession) -> list[ZonaAlumbradoOut]:
    zonas = sorted(await _all(db, ZonaAlumbrado), key=lambda z: -z.luminarias)
    return [ZonaAlumbradoOut.model_validate(z) for z in zonas]


async def alumbrado_cuadros(db: AsyncSession) -> list[CuadroMandoOut]:
    cuadros = sorted(await _all(db, CuadroMando), key=lambda c: c.codigo)
    return [CuadroMandoOut.model_validate(c) for c in cuadros]


async def alumbrado_luminarias(
    db: AsyncSession,
    zona: str | None = None,
    estado: str | None = None,
    tecnologia: str | None = None,
    buscar: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> LuminariasPage:
    q = select(Luminaria)
    if zona:
        q = q.where(Luminaria.zona_id == zona)
    if estado:
        q = q.where(Luminaria.estado == estado)
    if tecnologia:
        q = q.where(Luminaria.tecnologia == tecnologia)
    if buscar:
        like = f"%{buscar}%"
        q = q.where(Luminaria.codigo.ilike(like) | Luminaria.direccion.ilike(like))
    total = int((await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one())
    rows = (
        await db.execute(
            q.order_by(Luminaria.codigo).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return LuminariasPage(
        total=total, page=page, page_size=page_size,
        items=[LuminariaOut.model_validate(r) for r in rows],
    )


# ---------------------------------------------------------------------- AGUA
async def agua_overview(db: AsyncSession) -> AguaOverview:
    secs = sorted(await _all(db, SectorAgua), key=lambda s: s.codigo)
    contadores = sum(s.contadores for s in secs)
    tele = sum(s.contadores_telelectura for s in secs)
    caudal = float(sum(float(s.caudal_entrada_ls) for s in secs))
    fugas = sum(s.fugas_detectadas for s in secs)
    rend = [float(s.rendimiento_pct) for s in secs if s.rendimiento_pct is not None]
    return AguaOverview(
        sectores=len(secs), contadores=contadores, contadores_telelectura=tele,
        pct_telelectura=_pct(tele, contadores), caudal_total_ls=round(caudal, 1),
        fugas_detectadas=fugas,
        rendimiento_medio_pct=round(sum(rend) / len(rend), 1) if rend else 0.0,
        sectores_en_alerta=sum(1 for s in secs if s.estado != "operativo"),
        detalle=[SectorAguaOut.model_validate(s) for s in secs],
    )


# ------------------------------------------------------------------ RESIDUOS
async def residuos_overview(db: AsyncSession) -> ResiduosOverview:
    cont = await _all(db, Contenedor)
    total = len(cont)
    con_sensor = sum(1 for c in cont if c.tiene_sensor)
    llenos = [c.llenado_pct for c in cont if c.tiene_sensor and c.llenado_pct is not None]
    alto = sum(1 for v in llenos if v >= 80)
    por_frac = Counter(c.fraccion for c in cont)
    rutas = len({c.ruta for c in cont if c.ruta})
    return ResiduosOverview(
        total=total, con_sensor=con_sensor, pct_sensor=_pct(con_sensor, total),
        llenado_alto=alto, llenado_medio_pct=round(sum(llenos) / len(llenos), 1) if llenos else 0.0,
        rutas=rutas, por_fraccion=dict(por_frac),
    )


async def residuos_contenedores(
    db: AsyncSession,
    zona: str | None = None,
    fraccion: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> ContenedoresPage:
    q = select(Contenedor)
    if zona:
        q = q.where(Contenedor.zona_id == zona)
    if fraccion:
        q = q.where(Contenedor.fraccion == fraccion)
    total = int((await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one())
    rows = (
        await db.execute(
            q.order_by(Contenedor.codigo).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return ContenedoresPage(
        total=total, page=page, page_size=page_size,
        items=[ContenedorOut.model_validate(r) for r in rows],
    )


# ----------------------------------------------------------------- MOVILIDAD
async def movilidad_overview(db: AsyncSession) -> MovilidadOverview:
    pts = sorted(await _all(db, PuntoMovilidad), key=lambda p: p.codigo)
    aforos = [p for p in pts if p.tipo == "aforo"]
    parkings = [p for p in pts if p.tipo == "parking"]
    ev = [p for p in pts if p.tipo == "recarga_ev"]
    plazas_tot = sum(p.capacidad or 0 for p in parkings)
    plazas_occ = sum(p.valor_actual or 0 for p in parkings)
    tomas_libres = sum((p.capacidad or 0) - (p.valor_actual or 0) for p in ev)
    return MovilidadOverview(
        puntos=len(pts), aforos=len(aforos),
        trafico_actual_veh_h=sum(p.valor_actual or 0 for p in aforos),
        parkings=len(parkings), plazas_totales=plazas_tot, plazas_ocupadas=plazas_occ,
        ocupacion_parking_pct=_pct(plazas_occ, plazas_tot),
        puntos_recarga_ev=len(ev), tomas_ev_libres=tomas_libres,
        detalle=[PuntoMovilidadOut.model_validate(p) for p in pts],
    )


# ----------------------------------------------------------------- SEGURIDAD
async def seguridad_overview(db: AsyncSession) -> SeguridadOverview:
    cams = sorted(await _all(db, CamaraCCTV), key=lambda c: c.codigo)
    online = sum(1 for c in cams if c.estado == "operativo")
    sincom = sum(1 for c in cams if c.estado == "sin_comunicacion")
    return SeguridadOverview(
        camaras=len(cams), online=online, sin_comunicacion=sincom,
        pct_online=_pct(online, len(cams)),
        con_analitica=sum(1 for c in cams if c.con_analitica),
        retencion_dias=max((c.retencion_dias for c in cams), default=30),
        detalle=[CamaraCCTVOut.model_validate(c) for c in cams],
    )


# ------------------------------------------------------------------- ENERGÍA
async def energia_overview(db: AsyncSession) -> EnergiaOverview:
    sums = await _all(db, SuministroEnergia)
    consumo = float(sum(float(s.consumo_mes_kwh) for s in sums))
    auto = float(sum(float(s.autoconsumo_mes_kwh) for s in sums))
    coste = float(sum(float(s.coste_mes_eur) for s in sums))
    edificios = len({s.edificio.split(" (CUPS")[0] for s in sums})
    return EnergiaOverview(
        cups=len(sums), edificios=edificios, consumo_mes_kwh=round(consumo, 1),
        autoconsumo_mes_kwh=round(auto, 1), autoconsumo_pct=_pct(auto, consumo + auto),
        coste_mes_eur=round(coste, 2),
        cups_con_fotovoltaica=sum(1 for s in sums if s.tiene_fotovoltaica),
        coste_medio_kwh=round(coste / consumo, 3) if consumo else 0.0,
    )


async def energia_suministros(
    db: AsyncSession, page: int = 1, page_size: int = 25
) -> SuministrosPage:
    q = select(SuministroEnergia)
    total = int((await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one())
    rows = (
        await db.execute(
            q.order_by(SuministroEnergia.edificio).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return SuministrosPage(
        total=total, page=page, page_size=page_size,
        items=[SuministroEnergiaOut.model_validate(r) for r in rows],
    )


async def seguridad_camaras(db: AsyncSession) -> list[CamaraCCTVOut]:
    cams = sorted(await _all(db, CamaraCCTV), key=lambda c: c.codigo)
    return [CamaraCCTVOut.model_validate(c) for c in cams]


async def movilidad_puntos(db: AsyncSession) -> list[PuntoMovilidadOut]:
    pts = sorted(await _all(db, PuntoMovilidad), key=lambda p: p.codigo)
    return [PuntoMovilidadOut.model_validate(p) for p in pts]


async def agua_sectores(db: AsyncSession) -> list[SectorAguaOut]:
    secs = sorted(await _all(db, SectorAgua), key=lambda s: s.codigo)
    return [SectorAguaOut.model_validate(s) for s in secs]
