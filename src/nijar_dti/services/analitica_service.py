"""KPIs analíticos avanzados del observatorio Big Data (A.3).

Implementa dos indicadores exigidos por el Pliego:

- ``nps_proxy`` — índice tipo NPS como proxy de satisfacción.
- ``composicion_linguistica`` — aproximación al origen del visitante por
  convergencia de señales lingüísticas, con k-anonimato aplicado.

La lógica de cálculo se factoriza en funciones puras (``calcular_nps``,
``banda_confianza_pp``, ``componer_idiomas``) testeables sin base de datos.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.anonimizacion import K_ANONIMATO_MIN, suprimir_k_anonimato
from nijar_dti.models.faq import InteraccionChatbot
from nijar_dti.models.opinion import Opinion
from nijar_dti.models.visita import Visita
from nijar_dti.schemas.analitica import (
    ComposicionLinguistica,
    IdiomaComposicion,
    NPSComponente,
    NPSProxy,
)

# Canales de visita que representan a un visitante final (no telemetría interna)
_CANALES_VISITANTE = ("totem", "app", "web")


# --------------------------- Funciones puras ---------------------------


def calcular_nps(promotores: int, pasivos: int, detractores: int) -> float:
    """NPS = %promotores − %detractores, redondeado a 1 decimal.

    Devuelve 0.0 si la muestra es vacía (sin promotores ni detractores).
    """
    muestra = promotores + pasivos + detractores
    if muestra <= 0:
        return 0.0
    return round((promotores - detractores) * 100 / muestra, 1)


def banda_confianza_pp(conteo: int, total: int, z: float = 1.96) -> float:
    """Semiamplitud del intervalo de confianza (95 %) de una proporción.

    Expresada en puntos porcentuales. Usa la aproximación normal de Wald,
    suficiente para comunicar la incertidumbre por tamaño de muestra en el
    dashboard. Devuelve 0.0 si no hay muestra.
    """
    if total <= 0 or conteo < 0:
        return 0.0
    p = conteo / total
    return round(z * math.sqrt(max(p * (1 - p), 0.0) / total) * 100, 2)


def componer_idiomas(
    conteos: Counter[str], k: int = K_ANONIMATO_MIN
) -> tuple[list[IdiomaComposicion], int, int]:
    """Convierte un Counter de idiomas en la composición publicable.

    Aplica k-anonimato y calcula porcentaje y banda de confianza sobre el
    total ORIGINAL (incluidos los suprimidos), para que los porcentajes sean
    honestos respecto a la muestra real observada.

    Devuelve ``(lista, total_original, registros_suprimidos)``.
    """
    total_original = sum(max(n, 0) for n in conteos.values())
    publicables, suprimido = suprimir_k_anonimato(conteos, k)
    base = total_original or 1
    lista = [
        IdiomaComposicion(
            idioma=idioma,
            conteo=n,
            porcentaje=round(n * 100 / base, 2),
            banda_confianza_pp=banda_confianza_pp(n, base),
        )
        for idioma, n in sorted(publicables.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return lista, total_original, suprimido


# --------------------------- Orquestación con BBDD ---------------------------


async def nps_proxy(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> NPSProxy:
    componentes: list[NPSComponente] = []

    # Señal 1 — sentimiento de menciones (RRSS + reseñas + encuestas)
    q_op = select(
        func.count(case((Opinion.sentimiento == "positivo", 1))).label("pro"),
        func.count(case((Opinion.sentimiento == "neutro", 1))).label("pas"),
        func.count(case((Opinion.sentimiento == "negativo", 1))).label("det"),
    )
    if desde:
        q_op = q_op.where(Opinion.publicado_en >= desde)
    if hasta:
        q_op = q_op.where(Opinion.publicado_en <= hasta)
    r_op = (await db.execute(q_op)).one()
    pro_op, pas_op, det_op = int(r_op.pro or 0), int(r_op.pas or 0), int(r_op.det or 0)
    if pro_op + pas_op + det_op > 0:
        componentes.append(
            NPSComponente(
                señal="menciones_sentimiento",
                promotores=pro_op,
                pasivos=pas_op,
                detractores=det_op,
                muestra=pro_op + pas_op + det_op,
                nps=calcular_nps(pro_op, pas_op, det_op),
            )
        )

    # Señal 2 — feedback útil/no-útil del chatbot (util True=promotor, False=detractor)
    q_cb = select(
        func.count(case((InteraccionChatbot.util.is_(True), 1))).label("pro"),
        func.count(case((InteraccionChatbot.util.is_(False), 1))).label("det"),
    )
    if desde:
        q_cb = q_cb.where(InteraccionChatbot.created_at >= desde)
    if hasta:
        q_cb = q_cb.where(InteraccionChatbot.created_at <= hasta)
    r_cb = (await db.execute(q_cb)).one()
    pro_cb, det_cb = int(r_cb.pro or 0), int(r_cb.det or 0)
    if pro_cb + det_cb > 0:
        componentes.append(
            NPSComponente(
                señal="chatbot_feedback",
                promotores=pro_cb,
                pasivos=0,
                detractores=det_cb,
                muestra=pro_cb + det_cb,
                nps=calcular_nps(pro_cb, 0, det_cb),
            )
        )

    promotores = pro_op + pro_cb
    pasivos = pas_op
    detractores = det_op + det_cb

    return NPSProxy(
        desde=desde,
        hasta=hasta,
        nps=calcular_nps(promotores, pasivos, detractores),
        promotores=promotores,
        pasivos=pasivos,
        detractores=detractores,
        muestra_total=promotores + pasivos + detractores,
        componentes=componentes,
    )


async def composicion_linguistica(
    db: AsyncSession,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    k: int = K_ANONIMATO_MIN,
) -> ComposicionLinguistica:
    conteos: Counter[str] = Counter()
    señales: list[str] = []

    # Señal A — idioma de visitas a tótem/app/web
    q_v = select(Visita.idioma, func.count().label("n")).where(
        Visita.idioma.is_not(None),
        Visita.canal.in_(_CANALES_VISITANTE),
    )
    if desde:
        q_v = q_v.where(Visita.ocurrido_en >= desde)
    if hasta:
        q_v = q_v.where(Visita.ocurrido_en <= hasta)
    q_v = q_v.group_by(Visita.idioma)
    filas_v = (await db.execute(q_v)).all()
    if filas_v:
        señales.append("visitas_totem_app_web")
        for idioma, n in filas_v:
            conteos[_normaliza_idioma(idioma)] += int(n)

    # Señal B — idioma de las interacciones del chatbot
    q_c = select(InteraccionChatbot.idioma, func.count().label("n")).where(
        InteraccionChatbot.idioma.is_not(None)
    )
    if desde:
        q_c = q_c.where(InteraccionChatbot.created_at >= desde)
    if hasta:
        q_c = q_c.where(InteraccionChatbot.created_at <= hasta)
    q_c = q_c.group_by(InteraccionChatbot.idioma)
    filas_c = (await db.execute(q_c)).all()
    if filas_c:
        señales.append("interacciones_chatbot")
        for idioma, n in filas_c:
            conteos[_normaliza_idioma(idioma)] += int(n)

    # Señal C — idioma de las menciones en RRSS sobre el destino
    q_o = select(Opinion.idioma, func.count().label("n")).where(
        Opinion.idioma.is_not(None)
    )
    if desde:
        q_o = q_o.where(Opinion.publicado_en >= desde)
    if hasta:
        q_o = q_o.where(Opinion.publicado_en <= hasta)
    q_o = q_o.group_by(Opinion.idioma)
    filas_o = (await db.execute(q_o)).all()
    if filas_o:
        señales.append("menciones_rrss")
        for idioma, n in filas_o:
            conteos[_normaliza_idioma(idioma)] += int(n)

    idiomas, total, suprimidos = componer_idiomas(conteos, k)
    return ComposicionLinguistica(
        desde=desde,
        hasta=hasta,
        muestra_total=total,
        idiomas=idiomas,
        señales_usadas=señales,
        k_anonimato=k,
        registros_suprimidos=suprimidos,
    )


def _normaliza_idioma(idioma: str | None) -> str:
    """Reduce el código de idioma a su parte primaria en minúsculas (es-ES → es)."""
    if not idioma:
        return "desconocido"
    return idioma.strip().lower().split("-")[0][:2] or "desconocido"
