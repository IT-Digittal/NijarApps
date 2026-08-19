"""Motor de recomendaciones ejecutivas para dirección.

Enfoque **mixto**: un motor de **reglas** deterministas sobre los KPIs reales y
un conmutador a **OpenAI** (`direccion_recomendaciones_engine`). Sin
`OPENAI_API_KEY` o ante cualquier error, OpenAI cae a reglas. El **estado**
(pendiente → aceptada/…) y el comentario de dirección se persisten por `clave`.
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.models.recomendacion_direccion import RecomendacionDireccion
from nijar_dti.models.usuario import Usuario
from nijar_dti.schemas.direccion import EstadoRecomendacion, Prioridad, RecomendacionIA
from nijar_dti.services import direccion_service

log = logging.getLogger(__name__)

# Orden de prioridad para ordenar la lista de mayor a menor urgencia.
_ORDEN: dict[Prioridad, int] = {"critica": 0, "alta": 1, "media": 2, "informativa": 3}
_PRIORIDADES = set(_ORDEN)


def _slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def _clave(area: str, titulo: str) -> str:
    return (_slug(area) + "--" + _slug(titulo))[:80]


def _reglas(k: dict[str, Any]) -> list[RecomendacionIA]:
    recs: list[RecomendacionIA] = []
    alum, agua, res, ener = k["alumbrado"], k["agua"], k["residuos"], k["energia"]
    big, inc = k["big_data"], k["incidencias"]

    if inc["criticas"] > 0:
        recs.append(
            RecomendacionIA(
                titulo="Resolver las incidencias críticas abiertas",
                area="Servicio público",
                prioridad="critica",
                justificacion=(
                    f"Hay {inc['criticas']} incidencia(s) crítica(s) que afectan al servicio."
                ),
                impacto="Evita degradación del servicio y reclamaciones ciudadanas.",
                accion="Elevar a seguimiento prioritario y confirmar resolución dentro del SLA.",
            )
        )
    if alum.sin_comunicacion > 0 or alum.cuadros_alerta > 0 or alum.incidencias_abiertas > 0:
        recs.append(
            RecomendacionIA(
                titulo="Priorizar renovación LED y revisión de cuadros en alumbrado",
                area="Alumbrado público",
                prioridad="alta",
                justificacion=(
                    f"{alum.sin_comunicacion} cuadro(s) sin comunicación, "
                    f"{alum.cuadros_alerta} en alerta y {alum.incidencias_abiertas} "
                    "incidencia(s) abiertas concentran el riesgo."
                ),
                impacto="Reduce averías, consumo energético y reclamaciones vecinales.",
                accion=(
                    "Incluir las zonas afectadas en el próximo lote de renovación "
                    "y revisar comunicaciones."
                ),
            )
        )
    if agua.fugas_detectadas > 0:
        recs.append(
            RecomendacionIA(
                titulo="Inspeccionar los sectores de agua con fugas",
                area="Ciclo del agua",
                prioridad="alta",
                justificacion=(
                    f"Se detectan {agua.fugas_detectadas} sector(es) con fuga o consumo anómalo."
                ),
                impacto="Reduce pérdidas de agua y sobrecoste; mejora el rendimiento de la red.",
                accion=(
                    "Programar inspección y comparar el consumo con el mismo periodo "
                    "del año anterior."
                ),
            )
        )
    if res.llenado_alto >= 20:
        recs.append(
            RecomendacionIA(
                titulo="Reforzar la recogida en zonas de mayor llenado",
                area="Residuos",
                prioridad="media",
                justificacion=f"{res.llenado_alto} contenedores superan el 80% de llenado.",
                impacto="Evita desbordamientos y quejas en zonas de alta demanda.",
                accion="Anticipar la recogida en los puntos críticos y ajustar rutas al llenado real.",
            )
        )
    if ener.autoconsumo_pct < 10:
        recs.append(
            RecomendacionIA(
                titulo="Ampliar el autoconsumo fotovoltaico municipal",
                area="Energía municipal",
                prioridad="media",
                justificacion=(
                    f"El autoconsumo actual es del {ener.autoconsumo_pct:.0f}%, con margen de mejora."
                ),
                impacto="Reduce el coste energético y las emisiones de los edificios municipales.",
                accion="Priorizar instalación FV en los edificios con mayor consumo diurno.",
            )
        )
    if big.sentimiento_medio is not None and big.sentimiento_medio < 0.1:
        recs.append(
            RecomendacionIA(
                titulo="Reforzar la comunicación y contenidos del destino",
                area="Turismo / reputación",
                prioridad="informativa",
                justificacion=(
                    f"El sentimiento medio en redes es {big.sentimiento_medio:+.2f}, "
                    "con margen de mejora."
                ),
                impacto="Mejora la percepción del destino y la experiencia del visitante.",
                accion="Actualizar contenidos del chatbot y potenciar el canal con mayor alcance.",
            )
        )

    if not recs:
        recs.append(
            RecomendacionIA(
                titulo="Mantener el plan de seguimiento actual",
                area="General",
                prioridad="informativa",
                justificacion="Todos los servicios están dentro de los parámetros esperados.",
                impacto="Sostiene la calidad del servicio y el ahorro conseguido.",
                accion="Continuar el seguimiento semanal y preparar la temporada alta.",
            )
        )
    return recs


def _con_clave(recs: list[RecomendacionIA]) -> list[RecomendacionIA]:
    for r in recs:
        r.clave = _clave(r.area, r.titulo)
    return recs


async def _merge_estados(db: AsyncSession, recs: list[RecomendacionIA]) -> list[RecomendacionIA]:
    """Aplica el estado/comentario persistido a las recomendaciones generadas."""
    if not recs:
        return recs
    claves = [r.clave for r in recs]
    filas = (
        (
            await db.execute(
                select(RecomendacionDireccion).where(RecomendacionDireccion.clave.in_(claves))
            )
        )
        .scalars()
        .all()
    )
    por_clave = {f.clave: f for f in filas}
    for r in recs:
        f = por_clave.get(r.clave)
        if f is not None:
            r.estado = f.estado  # type: ignore[assignment]
            r.comentario = f.comentario
    return recs


async def generar(db: AsyncSession) -> list[RecomendacionIA]:
    """Genera recomendaciones (reglas u OpenAI), con estados y orden por prioridad."""
    settings = get_settings()
    if settings.direccion_recomendaciones_engine == "openai" and settings.openai_api_key:
        recs = await generar_openai(db)
    else:
        recs = _con_clave(_reglas(await direccion_service._kpis(db)))
    await _merge_estados(db, recs)
    recs.sort(key=lambda r: _ORDEN.get(r.prioridad, 9))
    return recs


def _prompt_openai(k: dict[str, Any]) -> list[dict[str, str]]:
    contexto = {
        "estado_incidencias_criticas": k["incidencias"]["criticas"],
        "alumbrado_sin_comunicacion": k["alumbrado"].sin_comunicacion,
        "alumbrado_incidencias": k["alumbrado"].incidencias_abiertas,
        "agua_fugas": k["agua"].fugas_detectadas,
        "residuos_llenado_alto": k["residuos"].llenado_alto,
        "energia_autoconsumo_pct": k["energia"].autoconsumo_pct,
        "sentimiento_medio": k["big_data"].sentimiento_medio,
    }
    sistema = (
        "Eres analista de una Smart City municipal. A partir de los KPIs, propon "
        "de 3 a 5 recomendaciones ejecutivas para dirección política, en español y "
        "lenguaje no técnico. Devuelve SOLO un array JSON de objetos con las claves "
        "titulo, area, justificacion, impacto, prioridad (critica|alta|media|informativa), accion."
    )
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": "KPIs actuales: " + json.dumps(contexto, ensure_ascii=False)},
    ]


async def generar_openai(db: AsyncSession) -> list[RecomendacionIA]:
    """Genera recomendaciones con OpenAI; cae a reglas ante error o sin clave."""
    from nijar_dti.services import chatbot_openai_adapter, consumo_ia_service

    settings = get_settings()
    k = await direccion_service._kpis(db)
    if not settings.openai_api_key:
        return _con_clave(_reglas(k))
    try:
        t0 = time.perf_counter()
        texto, uso = await chatbot_openai_adapter._llamada_openai(settings, _prompt_openai(k))
        latencia_ms = int((time.perf_counter() - t0) * 1000)
        datos = json.loads(texto[texto.index("[") : texto.rindex("]") + 1])
        recs: list[RecomendacionIA] = []
        for d in datos:
            prioridad = d.get("prioridad") if d.get("prioridad") in _PRIORIDADES else "media"
            recs.append(
                RecomendacionIA(
                    titulo=str(d["titulo"])[:255],
                    area=str(d.get("area", "General"))[:80],
                    justificacion=str(d.get("justificacion", "")),
                    impacto=str(d.get("impacto", "")),
                    prioridad=prioridad,
                    accion=str(d.get("accion", "")),
                    motor="openai",
                )
            )
        if not recs:
            raise ValueError("respuesta OpenAI sin recomendaciones")
        try:
            await consumo_ia_service.registrar(
                db,
                modelo=settings.openai_model,
                servicio="recomendaciones_direccion",
                canal="panel",
                tokens_entrada=int(uso.get("prompt_tokens", 0)),
                tokens_salida=int(uso.get("completion_tokens", 0)),
                latencia_ms=latencia_ms,
            )
        except Exception:  # noqa: BLE001
            log.warning("No se pudo registrar el consumo de IA de recomendaciones", exc_info=True)
        return _con_clave(recs)
    except Exception:  # noqa: BLE001
        log.warning("Recomendaciones OpenAI fallaron — fallback a reglas", exc_info=True)
        return _con_clave(_reglas(k))


class RecomendacionNoEncontradaError(Exception):
    """No hay ninguna recomendación generada con esa clave."""


async def actualizar_estado(
    db: AsyncSession,
    clave: str,
    *,
    estado: EstadoRecomendacion | None = None,
    comentario: str | None = None,
    actor: Usuario | None = None,
) -> RecomendacionIA:
    """Persiste el estado/comentario de una recomendación (upsert por clave)."""
    recs = {r.clave: r for r in _con_clave(_reglas(await direccion_service._kpis(db)))}
    # También admitimos claves de recomendaciones ya persistidas (no vigentes).
    fila = (
        await db.execute(
            select(RecomendacionDireccion).where(RecomendacionDireccion.clave == clave)
        )
    ).scalar_one_or_none()
    if fila is None and clave not in recs:
        raise RecomendacionNoEncontradaError(f"No existe la recomendación '{clave}'")

    if fila is None:
        base = recs[clave]
        fila = RecomendacionDireccion(
            clave=clave,
            titulo=base.titulo,
            area=base.area,
            prioridad=base.prioridad,
            estado=estado or "pendiente",
            comentario=comentario,
        )
        if actor is not None:
            fila.created_by = actor.id
        db.add(fila)
    else:
        if estado is not None:
            fila.estado = estado
        if comentario is not None:
            fila.comentario = comentario
        if actor is not None:
            fila.updated_by = actor.id
    await db.commit()
    await db.refresh(fila)

    vigente = recs.get(clave)
    if vigente is not None:
        vigente.estado = fila.estado  # type: ignore[assignment]
        vigente.comentario = fila.comentario
        return vigente
    return RecomendacionIA(
        clave=fila.clave,
        titulo=fila.titulo,
        area=fila.area,
        justificacion="",
        impacto="",
        prioridad=fila.prioridad,
        accion="",
        estado=fila.estado,
        comentario=fila.comentario,
    )
