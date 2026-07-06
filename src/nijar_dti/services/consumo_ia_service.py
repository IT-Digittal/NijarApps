"""Servicio de registro y agregación del consumo de IA generativa."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.models.consumo_ia import ConsumoIA
from nijar_dti.schemas.dashboards import (
    ConsumoIADesglose,
    ConsumoIAPuntoDiario,
    ConsumoIAResumen,
)

# Precios por millón de tokens (USD). Se usan para la estimación de coste;
# si OpenAI cambia tarifas basta con actualizar esta tabla.
PRECIOS_USD_POR_MILLON: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}
PRECIO_DEFECTO = (0.50, 1.50)


def coste_estimado_usd(modelo: str, tokens_entrada: int, tokens_salida: int) -> float:
    """Coste estimado en USD según la tabla de precios por millón de tokens."""
    entrada, salida = PRECIOS_USD_POR_MILLON.get(modelo, PRECIO_DEFECTO)
    return round((tokens_entrada * entrada + tokens_salida * salida) / 1_000_000, 6)


async def registrar(
    db: AsyncSession,
    *,
    modelo: str,
    servicio: str,
    canal: str,
    idioma: str | None = None,
    tokens_entrada: int = 0,
    tokens_salida: int = 0,
    latencia_ms: int | None = None,
    interaccion_id: UUID | None = None,
    proveedor: str = "openai",
) -> ConsumoIA:
    """Persiste una llamada facturable a un modelo de IA."""
    consumo = ConsumoIA(
        proveedor=proveedor,
        modelo=modelo,
        servicio=servicio,
        canal=canal,
        idioma=idioma,
        tokens_entrada=tokens_entrada,
        tokens_salida=tokens_salida,
        coste_estimado_usd=coste_estimado_usd(modelo, tokens_entrada, tokens_salida),
        latencia_ms=latencia_ms,
        interaccion_id=interaccion_id,
    )
    db.add(consumo)
    await db.flush()
    return consumo


async def resumen(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> ConsumoIAResumen:
    """Agrega el consumo de IA del periodo (por defecto, últimos 30 días)."""
    hasta = hasta or datetime.now(UTC)
    desde = desde or (hasta - timedelta(days=30))
    filtro = (ConsumoIA.ocurrido_en >= desde, ConsumoIA.ocurrido_en <= hasta)

    totales = (
        await db.execute(
            select(
                func.count(ConsumoIA.id),
                func.coalesce(func.sum(ConsumoIA.tokens_entrada), 0),
                func.coalesce(func.sum(ConsumoIA.tokens_salida), 0),
                func.coalesce(func.sum(ConsumoIA.coste_estimado_usd), 0.0),
                func.avg(ConsumoIA.latencia_ms),
            ).where(*filtro)
        )
    ).one()

    async def _desglose(campo) -> list[ConsumoIADesglose]:
        filas = (
            await db.execute(
                select(
                    campo,
                    func.count(ConsumoIA.id),
                    func.coalesce(func.sum(ConsumoIA.tokens_entrada), 0),
                    func.coalesce(func.sum(ConsumoIA.tokens_salida), 0),
                    func.coalesce(func.sum(ConsumoIA.coste_estimado_usd), 0.0),
                )
                .where(*filtro)
                .group_by(campo)
                .order_by(func.sum(ConsumoIA.coste_estimado_usd).desc())
            )
        ).all()
        return [
            ConsumoIADesglose(
                clave=str(f[0] or "—"),
                llamadas=f[1],
                tokens_entrada=f[2],
                tokens_salida=f[3],
                coste_estimado_usd=round(float(f[4]), 4),
            )
            for f in filas
        ]

    dia = func.date_trunc("day", ConsumoIA.ocurrido_en)
    serie_filas = (
        await db.execute(
            select(
                dia,
                func.coalesce(func.sum(ConsumoIA.tokens_entrada + ConsumoIA.tokens_salida), 0),
                func.coalesce(func.sum(ConsumoIA.coste_estimado_usd), 0.0),
            )
            .where(*filtro)
            .group_by(dia)
            .order_by(dia)
        )
    ).all()

    return ConsumoIAResumen(
        desde=desde,
        hasta=hasta,
        llamadas=totales[0],
        tokens_entrada=totales[1],
        tokens_salida=totales[2],
        coste_estimado_usd=round(float(totales[3]), 4),
        latencia_media_ms=round(float(totales[4]), 0) if totales[4] is not None else None,
        por_servicio=await _desglose(ConsumoIA.servicio),
        por_canal=await _desglose(ConsumoIA.canal),
        por_modelo=await _desglose(ConsumoIA.modelo),
        serie_diaria=[
            ConsumoIAPuntoDiario(
                fecha=f[0].date(),
                tokens=f[1],
                coste_estimado_usd=round(float(f[2]), 4),
            )
            for f in serie_filas
        ],
    )
