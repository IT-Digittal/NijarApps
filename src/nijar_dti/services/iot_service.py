"""Lógica de negocio para ingesta IoT y consulta de sensores y observaciones."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.observacion import Observacion
from nijar_dti.models.sensor import Sensor
from nijar_dti.schemas.common import GeoPoint, PageParams
from nijar_dti.schemas.iot import IngestResponse, ObservacionIn, SensorOut


class IoTError(Exception):
    pass


class SensorNotFound(IoTError):
    pass


async def get_sensor_by_urn(db: AsyncSession, urn: str) -> Sensor | None:
    res = await db.execute(
        select(Sensor).where(Sensor.urn == urn).where(Sensor.deleted_at.is_(None))
    )
    return res.scalar_one_or_none()


async def ingerir_observacion(
    db: AsyncSession, payload: ObservacionIn
) -> IngestResponse:
    sensor = await get_sensor_by_urn(db, payload.sensor_urn)
    if sensor is None:
        raise SensorNotFound(f"Sensor con URN '{payload.sensor_urn}' no encontrado")

    # Validación de rango (si aplica)
    valido = True
    motivo: str | None = None
    if payload.valor is not None:
        if sensor.rango_minimo is not None and payload.valor < sensor.rango_minimo:
            valido = False
            motivo = f"valor {payload.valor} por debajo del mínimo {sensor.rango_minimo}"
        elif sensor.rango_maximo is not None and payload.valor > sensor.rango_maximo:
            valido = False
            motivo = f"valor {payload.valor} por encima del máximo {sensor.rango_maximo}"

    obs = Observacion(
        sensor_id=sensor.id,
        observado_en=payload.observado_en,
        valor=payload.valor,
        unidades=payload.unidades or sensor.unidades_medida,
        valores=payload.valores,
        valido=valido,
        motivo_invalidez=motivo,
        payload_original=payload.payload_original,
    )
    db.add(obs)
    await db.flush()
    await db.refresh(obs)
    return IngestResponse(observacion_id=obs.id, valido=valido, motivo_invalidez=motivo)


async def listar_sensores(
    db: AsyncSession,
    tipo: str | None,
    estado: str | None,
    page: PageParams,
) -> tuple[list[Sensor], int]:
    base = select(Sensor).where(Sensor.deleted_at.is_(None))
    if tipo:
        base = base.where(Sensor.tipo == tipo)
    if estado:
        base = base.where(Sensor.estado == estado)

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0
    )
    res = await db.execute(
        base.order_by(Sensor.nombre).offset(page.offset).limit(page.limit)
    )
    return list(res.scalars().all()), total


def _geojson_str_to_geopoint(geojson_str: str | None) -> GeoPoint | None:
    if not geojson_str:
        return None
    try:
        data = json.loads(geojson_str)
        if data.get("type") != "Point":
            return None
        return GeoPoint(type="Point", coordinates=data["coordinates"])
    except (ValueError, KeyError, TypeError):
        return None


async def _get_ubicacion_geojson(
    db: AsyncSession, id_value: UUID,
) -> str | None:
    sql = text("SELECT ST_AsGeoJSON(ubicacion) AS geojson FROM sensores WHERE id = :id")
    result = await db.execute(sql, {"id": id_value})
    row = result.first()
    if row is None or row[0] is None:
        return None
    return str(row[0])


async def sensor_to_out(db: AsyncSession, s: Sensor) -> SensorOut:
    geojson = await _get_ubicacion_geojson(db, s.id)
    return SensorOut(
        id=s.id,
        urn=s.urn,
        nombre=s.nombre,
        tipo=s.tipo,
        fabricante=s.fabricante,
        modelo=s.modelo,
        descripcion_ubicacion=s.descripcion_ubicacion,
        unidades_medida=s.unidades_medida,
        rango_minimo=s.rango_minimo,
        rango_maximo=s.rango_maximo,
        umbrales_alerta=s.umbrales_alerta,
        frecuencia_muestreo_seg=s.frecuencia_muestreo_seg,
        estado=s.estado,
        topic_mqtt=s.topic_mqtt,
        activo=s.activo,
        ubicacion=_geojson_str_to_geopoint(geojson),
        nivel_bateria=s.nivel_bateria,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


async def historico_observaciones(
    db: AsyncSession,
    sensor_id: UUID,
    desde: datetime | None,
    hasta: datetime | None,
    limit: int = 100,
) -> list[Observacion]:
    sensor = await db.get(Sensor, sensor_id)
    if sensor is None or sensor.deleted_at is not None:
        raise SensorNotFound(f"Sensor {sensor_id} no encontrado")

    q = select(Observacion).where(Observacion.sensor_id == sensor_id)
    if desde:
        q = q.where(Observacion.observado_en >= desde)
    if hasta:
        q = q.where(Observacion.observado_en <= hasta)
    q = q.order_by(Observacion.observado_en.desc()).limit(limit)
    res = await db.execute(q)
    return list(res.scalars().all())
