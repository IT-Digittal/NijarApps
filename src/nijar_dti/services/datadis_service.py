"""Integración Datadis: carga diaria de datos eléctricos en la vertical de Energía.

- **Pública** (sin credenciales si Datadis lo permite): consumo y contratos de
  todo el municipio por día, sector y tensión → ``energia_municipio_diario``.
- **Privada** (usuario de Datadis del Ayuntamiento o autorizado): suministros
  municipales (CUPS) → ``energia_suministros`` (marcados ``fuente=datadis``)
  y su curva horaria → ``energia_consumos_horarios``; el consumo del mes de
  cada suministro se recalcula desde la curva.

Todas las cargas son idempotentes (upsert): repetir un periodo actualiza los
valores. Cuando existen suministros reales de Datadis, la vertical de Energía
deja de mostrar los suministros de demostración.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.datadis import (
    ClienteDatadis,
    DatadisAutenticacionError,
    DatadisError,
    LecturaHoraria,
    RegistroPublico,
    normalizar,
    parsear_registro_publico,
)
from nijar_dti.core.logging import get_logger
from nijar_dti.models.energia_datadis import ConsumoHorarioEnergia, EnergiaMunicipioDiario
from nijar_dti.models.verticales import SuministroEnergia

logger = get_logger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
FUENTE = "datadis"
_CERROJO_CARGA = 178105  # pg_advisory_lock: una sola carga aunque haya varios workers


def datadis_configurado(settings: Settings | None = None) -> bool:
    """True si hay credenciales para la API privada."""
    s = settings or get_settings()
    return bool(s.datadis_usuario and s.datadis_password)


def nuevo_cliente(settings: Settings | None = None) -> ClienteDatadis:
    s = settings or get_settings()
    return ClienteDatadis(
        usuario=s.datadis_usuario,
        password=s.datadis_password,
        nif_autorizado=s.datadis_nif_autorizado,
        base_url=s.datadis_base_url,
        timeout_seconds=s.datadis_timeout_seconds,
    )


def filtros_publicos(settings: Settings | None = None, codigo: str | None = None) -> dict[str, str]:
    s = settings or get_settings()
    return {
        "community": s.datadis_comunidad,
        "provinceMunicipality": codigo if codigo is not None else s.datadis_municipio_codigo,
    }


def tramos_mensuales(desde: date, hasta: date) -> list[tuple[date, date]]:
    """Parte [desde, hasta] en tramos dentro de un mismo mes (límite de Datadis)."""
    tramos = []
    ini = desde
    while ini <= hasta:
        siguiente_mes = (ini.replace(day=28) + timedelta(days=4)).replace(day=1)
        fin = min(hasta, siguiente_mes - timedelta(days=1))
        tramos.append((ini, fin))
        ini = fin + timedelta(days=1)
    return tramos


def es_del_municipio(r: RegistroPublico, nombre: str) -> bool:
    """Las filas sin municipio se aceptan (la consulta ya va filtrada)."""
    return not r.municipio or normalizar(nombre) in normalizar(r.municipio)


# ------------------------------------------------------------- pública ----


async def cargar_publico(
    db: AsyncSession, cli: ClienteDatadis, desde: date, hasta: date
) -> dict[str, int]:
    """Descarga y guarda el agregado diario del municipio entre dos fechas."""
    s = get_settings()
    cuenta = {"filas": 0, "guardadas": 0, "otros_municipios": 0, "no_interpretables": 0}
    for ini, fin in tramos_mensuales(desde, hasta):
        crudas, _ = await cli.buscar_publico(ini, fin, filtros_publicos(s))
        agregado: dict[tuple[date, str, str], list[float]] = defaultdict(lambda: [0, 0.0])
        for fila in crudas:
            cuenta["filas"] += 1
            reg = parsear_registro_publico(fila)
            if reg is None:
                cuenta["no_interpretables"] += 1
                continue
            if not es_del_municipio(reg, s.datadis_municipio_nombre):
                cuenta["otros_municipios"] += 1
                continue
            acc = agregado[(reg.fecha, reg.sector, reg.tension)]
            acc[0] += reg.contratos
            acc[1] += reg.energia_kwh
        for (fecha, sector, tension), (contratos, energia) in agregado.items():
            stmt = insert(EnergiaMunicipioDiario).values(
                id=uuid4(),  # insert() de Core no aplica el default_factory del ORM
                fecha=fecha,
                sector=sector,
                tension=tension,
                contratos=int(contratos),
                energia_kwh=round(energia, 3),
                municipio=s.datadis_municipio_nombre,
                fuente=FUENTE,
            )
            await db.execute(
                stmt.on_conflict_do_update(
                    constraint="uq_energia_municipio_dia",
                    set_={
                        "contratos": stmt.excluded.contratos,
                        "energia_kwh": stmt.excluded.energia_kwh,
                        "updated_at": func.now(),
                    },
                )
            )
            cuenta["guardadas"] += 1
    if cuenta["otros_municipios"]:
        logger.warning(
            "Datadis devolvió filas de otros municipios: revisar DATADIS_MUNICIPIO_CODIGO",
            descartadas=cuenta["otros_municipios"],
        )
    return cuenta


# ------------------------------------------------------------- privada ----


def momento_utc(lectura: LecturaHoraria) -> datetime:
    """Inicio de la hora en UTC. Datadis numera las horas 1..24 (hora de fin)."""
    local = datetime.combine(lectura.fecha, time(0), tzinfo=MADRID) + timedelta(
        hours=lectura.hora - 1
    )
    return local.astimezone(UTC)


async def cargar_privado(
    db: AsyncSession, cli: ClienteDatadis, mes_desde: str, mes_hasta: str
) -> dict[str, int]:
    """Suministros municipales + curva horaria entre dos meses (``AAAA/MM``)."""
    cuenta = {"suministros": 0, "nuevos": 0, "lecturas": 0, "errores": 0}
    suministros = await cli.suministros()
    for sm in suministros:
        cuenta["suministros"] += 1
        obj = (
            await db.execute(select(SuministroEnergia).where(SuministroEnergia.cups == sm.cups))
        ).scalar_one_or_none()
        metadatos = {
            "fuente": FUENTE,
            "distribuidora": sm.distribuidora,
            "codigo_distribuidora": sm.codigo_distribuidora,
            "tipo_punto": sm.tipo_punto,
            "municipio": sm.municipio,
            "codigo_postal": sm.codigo_postal,
            "valido_desde": sm.valido_desde,
            "valido_hasta": sm.valido_hasta,
        }
        if obj is None:
            obj = SuministroEnergia(cups=sm.cups, edificio=sm.direccion[:160], metadatos=metadatos)
            db.add(obj)
            cuenta["nuevos"] += 1
        else:
            obj.metadatos = {**(obj.metadatos or {}), **metadatos}
        try:
            potencia = await cli.potencia_contratada(sm)
            if potencia is not None:
                obj.potencia_contratada_kw = potencia
            lecturas = await cli.curva_horaria(sm, mes_desde, mes_hasta)
        except DatadisAutenticacionError:
            raise
        except DatadisError as exc:
            cuenta["errores"] += 1
            logger.warning("Datadis: fallo en suministro", cups=sm.cups, error=str(exc))
            continue
        for lec in lecturas:
            stmt = insert(ConsumoHorarioEnergia).values(
                id=uuid4(),
                cups=lec.cups or sm.cups,
                momento=momento_utc(lec),
                consumo_kwh=lec.consumo_kwh,
                excedente_kwh=lec.excedente_kwh,
                autoconsumo_kwh=lec.autoconsumo_kwh,
                metodo=(lec.metodo or None) and str(lec.metodo)[:20],
            )
            await db.execute(
                stmt.on_conflict_do_update(
                    constraint="uq_energia_consumo_cups_momento",
                    set_={
                        "consumo_kwh": stmt.excluded.consumo_kwh,
                        "excedente_kwh": stmt.excluded.excedente_kwh,
                        "autoconsumo_kwh": stmt.excluded.autoconsumo_kwh,
                        "metodo": stmt.excluded.metodo,
                        "updated_at": func.now(),
                    },
                )
            )
            cuenta["lecturas"] += 1
    await db.flush()
    await recalcular_consumo_mes(db)
    return cuenta


async def recalcular_consumo_mes(db: AsyncSession, hoy: date | None = None) -> None:
    """Consumo y autoconsumo del mes en curso de cada suministro, desde la curva."""
    hoy = hoy or datetime.now(MADRID).date()
    inicio = datetime.combine(hoy.replace(day=1), time(0), tzinfo=MADRID).astimezone(UTC)
    filas = (
        await db.execute(
            select(
                ConsumoHorarioEnergia.cups,
                func.sum(ConsumoHorarioEnergia.consumo_kwh),
                func.sum(func.coalesce(ConsumoHorarioEnergia.autoconsumo_kwh, 0)),
            )
            .where(ConsumoHorarioEnergia.momento >= inicio)
            .group_by(ConsumoHorarioEnergia.cups)
        )
    ).all()
    por_cups = {c: (float(cons or 0), float(auto or 0)) for c, cons, auto in filas}
    reales = (
        await db.execute(
            select(SuministroEnergia).where(
                SuministroEnergia.metadatos["fuente"].as_string() == FUENTE
            )
        )
    ).scalars()
    for s in reales:
        cons, auto = por_cups.get(s.cups, (0.0, 0.0))
        s.consumo_mes_kwh = round(cons, 2)
        s.autoconsumo_mes_kwh = round(auto, 2)
        s.tiene_fotovoltaica = s.tiene_fotovoltaica or auto > 0


async def hay_suministros_reales(db: AsyncSession) -> bool:
    n = (
        await db.execute(
            select(func.count()).where(SuministroEnergia.metadatos["fuente"].as_string() == FUENTE)
        )
    ).scalar_one()
    return bool(n)


# ------------------------------------------------------------ consultas ----


async def serie_municipio(db: AsyncSession, desde: date, hasta: date) -> dict[str, Any]:
    """Serie diaria del municipio (total y por sector) para el panel."""
    filas = (
        await db.execute(
            select(
                EnergiaMunicipioDiario.fecha,
                EnergiaMunicipioDiario.sector,
                func.sum(EnergiaMunicipioDiario.energia_kwh),
                func.sum(EnergiaMunicipioDiario.contratos),
            )
            .where(
                and_(EnergiaMunicipioDiario.fecha >= desde, EnergiaMunicipioDiario.fecha <= hasta)
            )
            .group_by(EnergiaMunicipioDiario.fecha, EnergiaMunicipioDiario.sector)
            .order_by(EnergiaMunicipioDiario.fecha)
        )
    ).all()
    dias: dict[date, dict[str, Any]] = {}
    sectores: dict[str, float] = defaultdict(float)
    for fecha, sector, energia, contratos in filas:
        d = dias.setdefault(
            fecha, {"fecha": fecha, "energia_kwh": 0.0, "contratos": 0, "sectores": {}}
        )
        d["energia_kwh"] += float(energia or 0)
        d["contratos"] += int(contratos or 0)
        d["sectores"][sector] = round(float(energia or 0), 1)
        sectores[sector] += float(energia or 0)
    serie = list(dias.values())
    for d in serie:
        d["energia_kwh"] = round(d["energia_kwh"], 1)
    ultima = (await db.execute(select(func.max(EnergiaMunicipioDiario.fecha)))).scalar_one_or_none()
    return {
        "desde": desde,
        "hasta": hasta,
        "ultima_fecha_disponible": ultima,
        "energia_total_kwh": round(sum(d["energia_kwh"] for d in serie), 1),
        "contratos_ultimo_dia": serie[-1]["contratos"] if serie else None,
        "por_sector_kwh": {k: round(v, 1) for k, v in sorted(sectores.items())},
        "serie": serie,
    }


async def curva_suministro(
    db: AsyncSession, cups: str, desde: datetime, hasta: datetime
) -> list[dict[str, Any]]:
    filas = (
        await db.execute(
            select(ConsumoHorarioEnergia)
            .where(
                ConsumoHorarioEnergia.cups == cups.upper(),
                ConsumoHorarioEnergia.momento >= desde,
                ConsumoHorarioEnergia.momento < hasta,
            )
            .order_by(ConsumoHorarioEnergia.momento)
        )
    ).scalars()
    return [
        {
            "momento": f.momento,
            "consumo_kwh": float(f.consumo_kwh),
            "autoconsumo_kwh": float(f.autoconsumo_kwh) if f.autoconsumo_kwh is not None else None,
            "excedente_kwh": float(f.excedente_kwh) if f.excedente_kwh is not None else None,
            "metodo": f.metodo,
        }
        for f in filas
    ]


# --------------------------------------------------------- carga diaria ----


def ventana_por_defecto(hoy: date) -> tuple[date, date, str, str]:
    """Pública: del día 1 del mes (o del anterior en los 5 primeros días) a ayer.
    Privada: mes actual (y el anterior en los 5 primeros días)."""
    ayer = hoy - timedelta(days=1)
    inicio = hoy.replace(day=1)
    if hoy.day <= 5:
        inicio = (inicio - timedelta(days=1)).replace(day=1)
    return inicio, ayer, inicio.strftime("%Y/%m"), hoy.strftime("%Y/%m")


async def ejecutar_carga(
    db: AsyncSession,
    *,
    publico_desde: date | None = None,
    publico_hasta: date | None = None,
    mes_desde: str | None = None,
    mes_hasta: str | None = None,
    solo: str | None = None,
) -> dict[str, Any]:
    """Carga pública y/o privada. No propaga errores de Datadis: los resume."""
    s = get_settings()
    ini, fin, m_ini, m_fin = ventana_por_defecto(datetime.now(MADRID).date())
    resultado: dict[str, Any] = {}
    async with nuevo_cliente(s) as cli:
        if solo in (None, "publico") and s.datadis_publico_activo:
            try:
                resultado["publico"] = await cargar_publico(
                    db, cli, publico_desde or ini, publico_hasta or fin
                )
            except DatadisError as exc:
                resultado["publico"] = {"error": str(exc)}
        if solo in (None, "privado"):
            if not datadis_configurado(s):
                resultado["privado"] = {"omitido": "sin DATADIS_USUARIO/DATADIS_PASSWORD"}
            else:
                try:
                    resultado["privado"] = await cargar_privado(
                        db, cli, mes_desde or m_ini, mes_hasta or m_fin
                    )
                except DatadisError as exc:
                    resultado["privado"] = {"error": str(exc)}
    return resultado


def _segundos_hasta(hora: int, ahora: datetime | None = None) -> float:
    ahora = ahora or datetime.now(MADRID)
    objetivo = ahora.replace(hour=hora, minute=0, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    return (objetivo - ahora).total_seconds()


async def carga_diaria_loop(hora: int) -> None:
    """Carga Datadis una vez al día a la hora indicada (hora de Madrid).

    No se ejecuta al arrancar: Datadis rechaza repetir la misma consulta privada
    en 24 h y los despliegues reinician la API. Con varios workers, un cerrojo
    de PostgreSQL garantiza una única carga.
    """
    from nijar_dti.core.database import AsyncSessionLocal

    while True:
        await asyncio.sleep(_segundos_hasta(hora))
        try:
            async with AsyncSessionLocal() as db:
                libre = (
                    await db.execute(
                        text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": _CERROJO_CARGA}
                    )
                ).scalar()
                if not libre:
                    continue  # otro worker ya está cargando
                resultado = await ejecutar_carga(db)
                await db.commit()
            logger.info("Carga diaria de Datadis", **resultado)
        except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
            logger.error("Error en la carga diaria de Datadis", error=str(exc))
        await asyncio.sleep(60)  # evita repetir dentro del mismo minuto
