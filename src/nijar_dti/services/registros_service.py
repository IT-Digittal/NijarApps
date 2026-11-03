"""Registro de eventos de las verticales: escribir, consultar con filtros y exportar.

Quién escribe registros:

- **Detector de cambios** (``detectar_cambios``, cada ``REGISTROS_DETECCION_MINUTOS``):
  compara el estado actual de cámaras, contenedores, puntos de movilidad,
  sectores de agua, cuadros de alumbrado y suministros eléctricos con el último
  conocido (``estados_activos``) y registra solo las transiciones: «CCTV-07 sin
  comunicación», «RSU-0214 supera el 90 %», «parking al 95 %»…
- **Lecturas IoT** (MQTT / API ``/data/iot``) de videocámaras, aforos y alumbrado.
- **Cargas de Datadis** (por suministro: lecturas cargadas o error) y la
  **importación del inventario de alumbrado** de WeLight.
- **Demo**: las verticales aún sin integrar arrancan con una semana de registros
  de ejemplo (``demo=True``) que la pantalla etiqueta como tales.

Los registros antiguos se purgan pasados ``REGISTROS_RETENCION_DIAS``.
"""

from __future__ import annotations

import asyncio
import csv
import io
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.core.logging import get_logger
from nijar_dti.models.alumbrado import SIN_TELEMETRIA, CuadroMando
from nijar_dti.models.registro_vertical import EstadoActivo, RegistroVertical
from nijar_dti.models.verticales import CamaraCCTV, Contenedor, PuntoMovilidad, SectorAgua

logger = get_logger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
VERTICALES = ("alumbrado", "agua", "residuos", "movilidad", "seguridad", "energia")
TIPOS = ("alarma", "estado", "lectura", "carga", "incidencia", "sistema")
SEVERIDADES = ("info", "aviso", "critico")
_CERROJO_DETECCION = 19_002_026

# Vertical de cada tipo de sensor IoT (los que no pertenecen a una vertical no se registran)
VERTICAL_SENSOR = {"videocamara": "seguridad", "aforo": "movilidad", "alumbrado": "alumbrado"}


# ------------------------------------------------------------ escritura ------
async def registrar(
    db: AsyncSession,
    vertical: str,
    tipo: str,
    mensaje: str,
    *,
    severidad: str = "info",
    activo_codigo: str | None = None,
    activo_nombre: str | None = None,
    origen: str = "plataforma",
    datos: dict[str, Any] | None = None,
    momento: datetime | None = None,
    demo: bool = False,
) -> RegistroVertical:
    reg = RegistroVertical(
        vertical=vertical,
        tipo=tipo,
        severidad=severidad if severidad in SEVERIDADES else "info",
        mensaje=mensaje[:2000],
        momento=momento or datetime.now(UTC),
        activo_codigo=(activo_codigo or None) and str(activo_codigo)[:60],
        activo_nombre=(activo_nombre or None) and str(activo_nombre)[:200],
        origen=origen[:30],
        datos=datos,
        demo=demo,
    )
    db.add(reg)
    return reg


async def registrar_seguro(db: AsyncSession, *args: Any, **kwargs: Any) -> None:
    """Como ``registrar`` pero sin propagar errores (el registro nunca rompe el proceso)."""
    try:
        await registrar(db, *args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo escribir el registro", error=str(exc))


# ------------------------------------------------------------ consulta -------
@dataclass
class FiltrosRegistros:
    vertical: str
    tipo: str | None = None
    severidad: str | None = None
    activo: str | None = None
    buscar: str | None = None
    desde: datetime | None = None
    hasta: datetime | None = None
    incluir_demo: bool = True


def _condiciones(f: FiltrosRegistros) -> list[Any]:
    c: list[Any] = [RegistroVertical.vertical == f.vertical]
    if f.tipo:
        c.append(RegistroVertical.tipo == f.tipo)
    if f.severidad:
        c.append(RegistroVertical.severidad == f.severidad)
    if f.activo:
        patron = f"%{f.activo.strip()}%"
        c.append(
            or_(
                RegistroVertical.activo_codigo.ilike(patron),
                RegistroVertical.activo_nombre.ilike(patron),
            )
        )
    if f.buscar:
        c.append(RegistroVertical.mensaje.ilike(f"%{f.buscar.strip()}%"))
    if f.desde:
        c.append(RegistroVertical.momento >= f.desde)
    if f.hasta:
        c.append(RegistroVertical.momento < f.hasta)
    if not f.incluir_demo:
        c.append(RegistroVertical.demo.is_(False))
    return c


async def listar(
    db: AsyncSession, f: FiltrosRegistros, page: int = 1, page_size: int = 50
) -> tuple[list[RegistroVertical], int]:
    cond = _condiciones(f)
    total = int(
        (
            await db.execute(select(func.count()).select_from(RegistroVertical).where(*cond))
        ).scalar_one()
        or 0
    )
    filas = (
        (
            await db.execute(
                select(RegistroVertical)
                .where(*cond)
                .order_by(RegistroVertical.momento.desc(), RegistroVertical.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(filas), total


async def resumen(db: AsyncSession, vertical: str) -> dict[str, Any]:
    """Recuentos de las últimas 24 h y 7 días por tipo y severidad."""
    ahora = datetime.now(UTC)
    base = RegistroVertical.vertical == vertical

    async def contar(desde: datetime, *extra: Any) -> int:
        q = select(func.count()).where(base, RegistroVertical.momento >= desde, *extra)
        return int((await db.execute(q)).scalar_one() or 0)

    por_tipo = {
        str(t): int(n)
        for t, n in (
            await db.execute(
                select(RegistroVertical.tipo, func.count())
                .where(base, RegistroVertical.momento >= ahora - timedelta(days=7))
                .group_by(RegistroVertical.tipo)
            )
        ).all()
    }
    ultimo = (
        await db.execute(select(func.max(RegistroVertical.momento)).where(base))
    ).scalar_one_or_none()
    demo = int(
        (
            await db.execute(select(func.count()).where(base, RegistroVertical.demo.is_(True)))
        ).scalar_one()
        or 0
    )
    total = int((await db.execute(select(func.count()).where(base))).scalar_one() or 0)
    return {
        "vertical": vertical,
        "ultimas_24h": await contar(ahora - timedelta(hours=24)),
        "criticos_24h": await contar(
            ahora - timedelta(hours=24), RegistroVertical.severidad == "critico"
        ),
        "avisos_24h": await contar(
            ahora - timedelta(hours=24), RegistroVertical.severidad == "aviso"
        ),
        "ultimos_7d": await contar(ahora - timedelta(days=7)),
        "por_tipo_7d": por_tipo,
        "ultimo": ultimo,
        "total": total,
        "solo_demo": total > 0 and demo == total,
    }


def csv_registros(filas: list[RegistroVertical]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        ["Fecha y hora", "Tipo", "Severidad", "Activo", "Nombre", "Mensaje", "Origen", "Demo"]
    )
    for r in filas:
        w.writerow(
            [
                r.momento.astimezone(MADRID).strftime("%d/%m/%Y %H:%M:%S"),
                r.tipo,
                r.severidad,
                r.activo_codigo or "",
                r.activo_nombre or "",
                r.mensaje,
                r.origen,
                "sí" if r.demo else "no",
            ]
        )
    return "﻿" + buf.getvalue()


# ------------------------------------------------------- detector de cambios --
@dataclass(frozen=True)
class EstadoObservado:
    vertical: str
    codigo: str
    nombre: str
    estado: str  # clave comparable (p. ej. "sin_comunicacion" o "llenado:90")
    tipo: str
    severidad: str
    mensaje: str
    datos: dict[str, Any] | None = None


def nivel(valor: float | None, cortes: tuple[int, ...] = (80, 90)) -> int:
    """Tramo de un porcentaje: 0 por debajo del primer corte, luego el corte superado."""
    if valor is None:
        return 0
    superados = [c for c in cortes if valor >= c]
    return max(superados) if superados else 0


_TXT_ESTADO = {
    "operativo": "vuelve a estar operativo",
    "operativa": "vuelve a estar operativa",
    "alerta": "en alerta",
    "averia": "en avería",
    "sin_comunicacion": "sin comunicación",
    "fuga": "con fuga detectada",
    "vigilancia": "en vigilancia",
    "mantenimiento": "en mantenimiento",
}


def _severidad_estado(estado: str) -> str:
    if estado in {"averia", "sin_comunicacion", "fuga"}:
        return "critico"
    if estado in {"operativo", "operativa"}:
        return "info"
    return "aviso"


def estados_observados(
    camaras: list[Any],
    contenedores: list[Any],
    puntos: list[Any],
    sectores: list[Any],
    cuadros: list[Any],
) -> list[EstadoObservado]:
    """Estado comparable de cada activo y el texto a registrar si cambia."""
    obs: list[EstadoObservado] = []
    for c in camaras:
        e = str(c.estado)
        obs.append(
            EstadoObservado(
                "seguridad",
                c.codigo,
                c.nombre,
                e,
                "estado",
                _severidad_estado(e),
                f"Cámara {c.codigo} · {c.nombre}: {_TXT_ESTADO.get(e, e.replace('_', ' '))}",
            )
        )
    for c in contenedores:
        if not c.tiene_sensor:
            continue
        n = nivel(c.llenado_pct)
        obs.append(
            EstadoObservado(
                "residuos",
                c.codigo,
                f"{c.fraccion} · {c.zona_id}",
                f"llenado:{n}",
                "alarma",
                "critico" if n >= 90 else ("aviso" if n else "info"),
                (
                    f"Contenedor {c.codigo} ({c.fraccion}) al {c.llenado_pct} %: supera el {n} %"
                    if n
                    else f"Contenedor {c.codigo} ({c.fraccion}) vaciado o por debajo del 80 %"
                ),
                {"llenado_pct": c.llenado_pct},
            )
        )
        e = str(c.estado)
        obs.append(
            EstadoObservado(
                "residuos",
                f"{c.codigo}#estado",
                c.codigo,
                e,
                "estado",
                _severidad_estado(e),
                f"Contenedor {c.codigo}: {_TXT_ESTADO.get(e, e.replace('_', ' '))}",
            )
        )
    for p in puntos:
        pct = (p.valor_actual or 0) / p.capacidad * 100 if p.capacidad else None
        n = nivel(pct, (85, 95))
        obs.append(
            EstadoObservado(
                "movilidad",
                p.codigo,
                p.nombre,
                f"ocupacion:{n}",
                "alarma",
                "critico" if n >= 95 else ("aviso" if n else "info"),
                (
                    f"{p.nombre} al {pct:.0f} % de su capacidad ({p.valor_actual} de {p.capacidad})"
                    if n and pct is not None
                    else f"{p.nombre} por debajo del 85 % de ocupación"
                ),
                {"valor": p.valor_actual, "capacidad": p.capacidad},
            )
        )
    for s in sectores:
        e = "fuga" if (s.fugas_detectadas or 0) > 0 else str(s.estado)
        obs.append(
            EstadoObservado(
                "agua",
                s.codigo,
                s.nombre,
                e,
                "alarma" if e == "fuga" else "estado",
                _severidad_estado(e),
                (
                    f"Sector {s.codigo} · {s.nombre}: {s.fugas_detectadas} fuga(s) detectada(s)"
                    if e == "fuga"
                    else f"Sector {s.codigo} · {s.nombre}: "
                    + _TXT_ESTADO.get(e, e.replace("_", " "))
                ),
                {
                    "rendimiento_pct": float(s.rendimiento_pct)
                    if s.rendimiento_pct is not None
                    else None
                },
            )
        )
    for q in cuadros:
        if q.comunicaciones == SIN_TELEMETRIA:
            continue  # inventario sin telegestión: no hay estado real que vigilar
        e = str(q.estado)
        alarmas = ", ".join(q.alarmas or [])
        obs.append(
            EstadoObservado(
                "alumbrado",
                q.codigo,
                q.nombre,
                e + ("|" + alarmas if alarmas else ""),
                "estado",
                _severidad_estado(e),
                f"Cuadro {q.codigo} · {q.nombre}: {_TXT_ESTADO.get(e, e.replace('_', ' '))}"
                + (f" ({alarmas})" if alarmas else ""),
            )
        )
    return obs


async def detectar_cambios(db: AsyncSession, *, demo: bool | None = None) -> int:
    """Registra las transiciones de estado desde la última pasada. Devuelve cuántas.

    La primera vez que se ve un activo solo se guarda su estado (no se registra:
    no es un cambio). ``demo`` marca los registros de verticales aún sin integrar.
    """
    from nijar_dti.services.direccion_panel_service import estado_datos

    camaras = list((await db.execute(select(CamaraCCTV))).scalars().all())
    contenedores = list((await db.execute(select(Contenedor))).scalars().all())
    puntos = list((await db.execute(select(PuntoMovilidad))).scalars().all())
    sectores = list((await db.execute(select(SectorAgua))).scalars().all())
    cuadros = list((await db.execute(select(CuadroMando))).scalars().all())
    observados = estados_observados(camaras, contenedores, puntos, sectores, cuadros)
    previos = {
        (v, c): e
        for v, c, e in (
            await db.execute(
                select(EstadoActivo.vertical, EstadoActivo.codigo, EstadoActivo.estado)
            )
        ).all()
    }
    est = await estado_datos(db)
    nuevos = 0
    for o in observados:
        clave = (o.vertical, o.codigo)
        anterior = previos.get(clave)
        if anterior == o.estado:
            continue
        if anterior is not None:
            await registrar(
                db,
                o.vertical,
                o.tipo,
                o.mensaje,
                severidad=o.severidad,
                activo_codigo=o.codigo.split("#")[0],
                activo_nombre=o.nombre,
                origen="detector",
                datos={**(o.datos or {}), "anterior": anterior, "actual": o.estado},
                demo=est.demo(o.vertical) if demo is None else demo,
            )
            nuevos += 1
        stmt = insert(EstadoActivo).values(
            id=uuid4(), vertical=o.vertical, codigo=o.codigo[:60], estado=o.estado[:60]
        )
        await db.execute(
            stmt.on_conflict_do_update(
                constraint="uq_estado_activo",
                set_={"estado": stmt.excluded.estado, "updated_at": func.now()},
            )
        )
    return nuevos


async def purgar(db: AsyncSession, dias: int) -> int:
    res = await db.execute(
        delete(RegistroVertical).where(
            RegistroVertical.momento < datetime.now(UTC) - timedelta(days=dias)
        )
    )
    return int(getattr(res, "rowcount", 0) or 0)


async def deteccion_loop(minutos: int) -> None:
    """Cada ``minutos`` detecta cambios de estado; una vez al día purga lo antiguo."""
    from nijar_dti.core.database import AsyncSessionLocal

    ultima_purga: datetime | None = None
    await asyncio.sleep(30)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                libre = (
                    await db.execute(
                        text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": _CERROJO_DETECCION}
                    )
                ).scalar()
                if libre:
                    n = await detectar_cambios(db)
                    ahora = datetime.now(UTC)
                    if ultima_purga is None or ahora - ultima_purga > timedelta(hours=24):
                        await purgar(db, get_settings().registros_retencion_dias)
                        ultima_purga = ahora
                    await db.commit()
                    if n:
                        logger.info("Registros: cambios de estado detectados", cambios=n)
        except Exception as exc:  # noqa: BLE001 — el bucle no debe morir
            logger.error("Error en el detector de registros", error=str(exc))
        await asyncio.sleep(minutos * 60)


# ------------------------------------------------------------ demo -----------
_DEMO_PLANTILLAS: dict[str, list[tuple[str, str, str]]] = {
    "seguridad": [
        ("alarma", "aviso", "Detección de persona en zona restringida (analítica de vídeo)"),
        ("alarma", "aviso", "Merodeo detectado más de 3 minutos"),
        ("alarma", "critico", "Pulsación de botón SOS"),
        ("estado", "critico", "Pérdida de comunicación con la cámara"),
        ("estado", "info", "Cámara de nuevo en línea"),
        ("lectura", "info", "Matrícula leída (LPR) en acceso al núcleo"),
        ("alarma", "aviso", "Sabotaje: cámara tapada o movida"),
        ("lectura", "info", "Conteo de personas en el último cuarto de hora"),
    ],
    "residuos": [
        ("alarma", "aviso", "Contenedor supera el 80 % de llenado"),
        ("alarma", "critico", "Contenedor supera el 90 % de llenado"),
        ("lectura", "info", "Contenedor vaciado (recogida registrada)"),
        ("alarma", "aviso", "Temperatura anómala en el contenedor"),
        ("estado", "aviso", "Sensor de llenado con batería baja"),
    ],
    "movilidad": [
        ("lectura", "info", "Paso de vehículos registrado en el aforo"),
        ("alarma", "aviso", "Aparcamiento al 85 % de ocupación"),
        ("alarma", "critico", "Aparcamiento completo"),
        ("estado", "info", "Punto de recarga disponible"),
        ("estado", "aviso", "Punto de recarga fuera de servicio"),
    ],
    "agua": [
        ("alarma", "critico", "Caudal nocturno anómalo: posible fuga"),
        ("alarma", "aviso", "Presión baja en el sector"),
        ("lectura", "info", "Lectura diaria de telelectura recibida"),
        ("estado", "aviso", "Contador sin comunicar más de 72 h"),
        ("alarma", "aviso", "Cloro residual por debajo del umbral"),
    ],
}


async def sembrar_demo(db: AsyncSession, dias: int = 7, por_dia: int = 40) -> int:
    """Una semana de registros de ejemplo para las verticales sin integrar."""
    rnd = random.Random(2026)  # noqa: S311 — datos de demostración, no criptografía
    activos = {
        "seguridad": [
            (c.codigo, c.nombre) for c in (await db.execute(select(CamaraCCTV))).scalars()
        ],
        "residuos": [
            (c.codigo, f"{c.fraccion} · {c.zona_id}")
            for c in (await db.execute(select(Contenedor).where(Contenedor.tiene_sensor))).scalars()
        ],
        "movilidad": [
            (p.codigo, p.nombre) for p in (await db.execute(select(PuntoMovilidad))).scalars()
        ],
        "agua": [(s.codigo, s.nombre) for s in (await db.execute(select(SectorAgua))).scalars()],
    }
    ahora = datetime.now(UTC)
    n = 0
    for vertical, plantillas in _DEMO_PLANTILLAS.items():
        lista: list[tuple[str | None, str | None]] = list(activos.get(vertical) or [])
        if not lista:
            lista = [(None, None)]
        for _ in range(dias * por_dia):
            tipo, sev, texto = rnd.choice(plantillas)
            codigo, nombre = rnd.choice(lista)
            momento = ahora - timedelta(minutes=rnd.randint(1, dias * 24 * 60))
            await registrar(
                db,
                vertical,
                tipo,
                texto,
                severidad=sev,
                activo_codigo=codigo,
                activo_nombre=nombre,
                origen="demo",
                momento=momento,
                demo=True,
            )
            n += 1
    return n
