"""Cuadro de Mando de Dirección — composición de KPIs ejecutivos.

Reúne los overviews de las verticales y los indicadores del observatorio para
producir una visión estratégica: estado global, semáforo por vertical, alertas
relevantes e impacto (económico, ciudadano, ambiental). Los valores económicos
y de CO₂ son estimaciones (factores en `config`), marcadas con `estimado=True`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.schemas.dashboards import BigDataOverview
from nijar_dti.schemas.direccion import (
    AlertaDireccion,
    EstadoVertical,
    ImpactoAmbiental,
    ImpactoCiudadano,
    ImpactoDireccion,
    ImpactoEconomico,
    KpiInteranual,
    ResumenMunicipal,
)
from nijar_dti.schemas.verticales import (
    AguaOverview,
    AlumbradoOverview,
    EnergiaOverview,
    MovilidadOverview,
    ResiduosOverview,
    SeguridadOverview,
)
from nijar_dti.services import (
    analitica_service,
    contexto_service,
    dashboards_service,
    incidencias_service,
    verticales_service,
)

# Indicadores turísticos con serie histórica oficial (contexto): permiten
# comparativa interanual real. offset = nº de periodos de un año (mensual=12,
# trimestral=4).
_INTERANUAL_TURISMO: list[tuple[str, str, str, str, str, int]] = [
    ("viajeros", "Viajeros alojados",
     "junta_andalucia", "viajeros_alojados", "provincia_almeria", 12),
    ("pernoctaciones", "Pernoctaciones",
     "ine_eoh", "pernoctaciones", "provincia_almeria", 12),
    ("gasto", "Gasto turístico",
     "ine_egatur", "gasto_turistico_total_eur", "andalucia", 4),
    ("pasajeros_aena", "Pasajeros aeropuerto Almería",
     "aena", "pasajeros_aeropuerto_almeria", "almeria", 12),
    ("turistas", "Turistas internacionales (Andalucía)",
     "ine_frontur", "turistas_internacionales", "andalucia", 12),
]


def _riesgo(estado: str) -> str:
    return {"verde": "bajo", "ambar": "medio", "rojo": "alto"}[estado]


def _semaforo_alumbrado(o: AlumbradoOverview) -> EstadoVertical:
    if o.en_averia > 30 or o.disponibilidad_pct < 90:
        estado = "rojo"
    elif o.sin_comunicacion > 0 or o.cuadros_alerta > 0 or o.incidencias_abiertas > 0:
        estado = "ambar"
    else:
        estado = "verde"
    rec = (
        "Priorizar zonas con concentración de incidencias y revisar cuadros sin comunicación."
        if estado != "verde"
        else "Mantener el plan de mantenimiento preventivo."
    )
    return EstadoVertical(
        clave="alumbrado", nombre="Alumbrado público", icono="bulb", estado=estado,
        indicador_clave=(
            f"{o.disponibilidad_pct:.1f}% disp. · {o.incidencias_abiertas} incidencias"
        ),
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_agua(o: AguaOverview) -> EstadoVertical:
    if o.sectores_en_alerta > 4:
        estado = "rojo"
    elif o.fugas_detectadas > 0 or o.sectores_en_alerta > 0:
        estado = "ambar"
    else:
        estado = "verde"
    rec = (
        "Inspeccionar los sectores con fugas o consumo nocturno anómalo."
        if estado != "verde"
        else "Continuar la telelectura y el seguimiento de rendimiento."
    )
    return EstadoVertical(
        clave="agua", nombre="Ciclo del agua", icono="drop", estado=estado,
        indicador_clave=f"{o.fugas_detectadas} fugas · rendimiento {o.rendimiento_medio_pct:.0f}%",
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_residuos(o: ResiduosOverview) -> EstadoVertical:
    estado = "ambar" if o.llenado_alto >= 20 else "verde"
    rec = (
        "Reforzar la recogida en las zonas con llenado recurrente > 80%."
        if estado != "verde"
        else "Mantener el seguimiento semanal de rutas."
    )
    return EstadoVertical(
        clave="residuos", nombre="Residuos", icono="trash", estado=estado,
        indicador_clave=f"{o.llenado_alto} contenedores ≥ 80% · media {o.llenado_medio_pct:.0f}%",
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_movilidad(o: MovilidadOverview) -> EstadoVertical:
    estado = "ambar" if o.ocupacion_parking_pct >= 90 else "verde"
    rec = (
        "Preparar refuerzo de aparcamiento y señalización en días de alta afluencia."
        if estado != "verde"
        else "Afluencia dentro de lo normal; preparar temporada alta."
    )
    return EstadoVertical(
        clave="movilidad", nombre="Movilidad", icono="car", estado=estado,
        indicador_clave=(
            f"{o.trafico_actual_veh_h} veh/h · ocup. parking {o.ocupacion_parking_pct:.0f}%"
        ),
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_seguridad(o: SeguridadOverview) -> EstadoVertical:
    estado = "ambar" if o.sin_comunicacion > 0 else "verde"
    rec = (
        "Revisar los dispositivos fuera de servicio en espacios sensibles."
        if estado != "verde"
        else "Cobertura CCTV operativa; mantener seguimiento."
    )
    return EstadoVertical(
        clave="seguridad", nombre="Seguridad", icono="cam", estado=estado,
        indicador_clave=(
            f"{o.pct_online:.0f}% cámaras online · {o.sin_comunicacion} sin comunicación"
        ),
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_energia(o: EnergiaOverview) -> EstadoVertical:
    # Vertical informativa: solo se marca en alerta si no hay ningún autoconsumo.
    estado = "ambar" if o.autoconsumo_pct <= 0 else "verde"
    rec = (
        "Ampliar autoconsumo fotovoltaico en edificios de mayor consumo diurno."
        if estado != "verde"
        else "Autoconsumo positivo; continuar la optimización."
    )
    return EstadoVertical(
        clave="energia", nombre="Energía municipal", icono="bolt", estado=estado,
        indicador_clave=f"{o.consumo_mes_kwh:,.0f} kWh/mes · autoconsumo {o.autoconsumo_pct:.0f}%",
        riesgo=_riesgo(estado), recomendacion=rec,
    )


def _semaforo_dti(big: BigDataOverview) -> EstadoVertical:
    s = big.sentimiento_medio if big.sentimiento_medio is not None else 0.0
    if s < -0.1:
        estado = "rojo"
    elif s < 0.1:
        estado = "ambar"
    else:
        estado = "verde"
    rec = (
        "Reforzar la comunicación del destino y actualizar contenidos del chatbot."
        if estado != "verde"
        else "Buena percepción del destino; potenciar los canales con más alcance."
    )
    return EstadoVertical(
        clave="dti", nombre="Turismo inteligente", icono="totem", estado=estado,
        indicador_clave=f"{big.menciones_ultimo_mes} menciones/mes · sentimiento {s:+.2f}",
        riesgo=_riesgo(estado), recomendacion=rec,
    )


async def _kpis(db: AsyncSession) -> dict[str, Any]:
    """Recopila los overviews e indicadores base (reutilizados por recomendaciones)."""
    return {
        "alumbrado": await verticales_service.alumbrado_overview(db),
        "agua": await verticales_service.agua_overview(db),
        "residuos": await verticales_service.residuos_overview(db),
        "movilidad": await verticales_service.movilidad_overview(db),
        "seguridad": await verticales_service.seguridad_overview(db),
        "energia": await verticales_service.energia_overview(db),
        "big_data": await dashboards_service.big_data_overview(db),
        "nps": await analitica_service.nps_proxy(db),
        "incidencias": incidencias_service.resumen_incidencias(
            await incidencias_service.listar_incidencias(db)
        ),
    }


def _construir_semaforo(k: dict[str, Any]) -> list[EstadoVertical]:
    return [
        _semaforo_dti(k["big_data"]),
        _semaforo_alumbrado(k["alumbrado"]),
        _semaforo_agua(k["agua"]),
        _semaforo_residuos(k["residuos"]),
        _semaforo_movilidad(k["movilidad"]),
        _semaforo_seguridad(k["seguridad"]),
        _semaforo_energia(k["energia"]),
    ]


def _alertas(k: dict[str, Any], semaforo: list[EstadoVertical]) -> list[AlertaDireccion]:
    alertas: list[AlertaDireccion] = []
    if k["incidencias"]["criticas"] > 0:
        alertas.append(AlertaDireccion(
            nivel="alto", area="Servicio público",
            motivo=f"{k['incidencias']['criticas']} incidencia(s) crítica(s) registradas",
            impacto="Posible afección al servicio y a la percepción ciudadana",
            recomendacion="Elevar a seguimiento prioritario y confirmar resolución en plazo.",
        ))
    if k["agua"].fugas_detectadas > 0:
        alertas.append(AlertaDireccion(
            nivel="medio", area="Ciclo del agua",
            motivo=f"{k['agua'].fugas_detectadas} sector(es) con fuga o consumo anómalo",
            impacto="Pérdida de agua y sobrecoste evitable",
            recomendacion="Priorizar inspección de los sectores afectados.",
        ))
    if k["alumbrado"].sin_comunicacion > 0 or k["alumbrado"].cuadros_alerta > 0:
        alertas.append(AlertaDireccion(
            nivel="medio", area="Alumbrado público",
            motivo=(
                f"{k['alumbrado'].sin_comunicacion} cuadro(s) sin comunicación / "
                f"{k['alumbrado'].cuadros_alerta} en alerta"
            ),
            impacto="Riesgo de averías y reclamaciones vecinales",
            recomendacion="Revisar los cuadros afectados y priorizar renovación LED.",
        ))
    if k["residuos"].llenado_alto >= 20:
        alertas.append(AlertaDireccion(
            nivel="medio", area="Residuos",
            motivo=f"{k['residuos'].llenado_alto} contenedores con llenado ≥ 80%",
            impacto="Riesgo de desbordamiento en zonas de alta demanda",
            recomendacion="Anticipar recogida en los puntos con mayor llenado.",
        ))
    big = k["big_data"]
    if big.sentimiento_medio is not None and big.sentimiento_medio < 0:
        alertas.append(AlertaDireccion(
            nivel="bajo", area="Turismo / reputación",
            motivo="Sentimiento negativo detectado en redes sobre el destino",
            impacto="Percepción pública del destino turístico",
            recomendacion="Revisar temas recurrentes y reforzar la comunicación.",
        ))
    return alertas


def _impacto(k: dict[str, Any]) -> ImpactoDireccion:
    s = get_settings()
    alum, ener, big, nps = k["alumbrado"], k["energia"], k["big_data"], k["nps"]

    # Ahorro energético estimado: LED frente a baseline VSAP + autoconsumo FV.
    ahorro_kwh_alumbrado = alum.consumo_mes_kwh * (s.baseline_consumo_vsap_factor - 1)
    ahorro_kwh = ahorro_kwh_alumbrado + ener.autoconsumo_mes_kwh
    ahorro_eur = round(ahorro_kwh * s.precio_kwh_eur, 0)
    coste_eur = round(ener.coste_mes_eur + alum.consumo_mes_kwh * s.precio_kwh_eur, 0)

    co2_evitado_t = round(ahorro_kwh * s.factor_co2_kwh_kg * 12 / 1000, 1)
    consumo_total_kwh = round(alum.consumo_mes_kwh + ener.consumo_mes_kwh, 0)

    satisfaccion = round((nps.nps + 100) / 2, 1)
    return ImpactoDireccion(
        economico=ImpactoEconomico(
            ahorro_estimado_eur_mes=ahorro_eur, coste_energetico_mes_eur=coste_eur, estimado=True
        ),
        ciudadano=ImpactoCiudadano(
            satisfaccion_pct=satisfaccion, nps=nps.nps,
            sentimiento_medio=big.sentimiento_medio, menciones_mes=big.menciones_ultimo_mes,
        ),
        ambiental=ImpactoAmbiental(
            co2_evitado_t_anio=co2_evitado_t, autoconsumo_pct=ener.autoconsumo_pct,
            consumo_energetico_kwh_mes=consumo_total_kwh, estimado=True,
        ),
    )


async def _interanual_turismo(db: AsyncSession) -> list[KpiInteranual]:
    """Comparativa "vs mismo periodo del año pasado" para turismo (contexto real)."""
    kpis: list[KpiInteranual] = []
    for clave, nombre, fuente, indicador, ambito, offset in _INTERANUAL_TURISMO:
        serie = await contexto_service.obtener_serie(db, fuente, indicador, ambito)
        pts = serie.puntos
        if len(pts) <= offset:
            continue  # sin histórico suficiente: no se inventa
        actual, anterior = pts[-1], pts[-1 - offset]
        if not anterior.valor:
            continue
        var = round((actual.valor - anterior.valor) / anterior.valor * 100, 1)
        tendencia = "sube" if var > 0.5 else ("baja" if var < -0.5 else "estable")
        kpis.append(KpiInteranual(
            clave=clave, nombre=nombre, fuente=fuente,
            periodo=actual.periodo, periodo_anterior=anterior.periodo,
            valor=actual.valor, valor_anterior=anterior.valor,
            variacion_pct=var, unidad=actual.unidad, tendencia=tendencia,
        ))
    return kpis


async def resumen_municipal(db: AsyncSession) -> ResumenMunicipal:
    k = await _kpis(db)
    semaforo = _construir_semaforo(k)
    alertas = _alertas(k, semaforo)
    impacto = _impacto(k)

    rojos = sum(1 for e in semaforo if e.estado == "rojo")
    ambares = sum(1 for e in semaforo if e.estado == "ambar")
    verdes = sum(1 for e in semaforo if e.estado == "verde")
    criticas = k["incidencias"]["criticas"]

    estado_global = max(0, min(100, round(100 - 8 * rojos - 3 * ambares - 4 * criticas)))
    estado_texto = (
        "correcto" if estado_global >= 85
        else "atencion" if estado_global >= 70
        else "critico"
    )

    disp = round(
        (
            k["alumbrado"].disponibilidad_pct
            + k["seguridad"].pct_online
            + k["agua"].rendimiento_medio_pct
        )
        / 3,
        1,
    )

    return ResumenMunicipal(
        estado_global=estado_global,
        estado_texto=estado_texto,
        servicios_ok=verdes,
        servicios_total=len(semaforo),
        areas_alerta=[e.nombre for e in semaforo if e.estado != "verde"],
        incidencias_criticas=criticas,
        disponibilidad_media_pct=disp,
        satisfaccion_pct=impacto.ciudadano.satisfaccion_pct,
        ahorro_estimado_eur_mes=impacto.economico.ahorro_estimado_eur_mes,
        co2_evitado_t_anio=impacto.ambiental.co2_evitado_t_anio,
        semaforo=semaforo,
        alertas=alertas,
        impacto=impacto,
        interanual_turismo=await _interanual_turismo(db),
        generado_en=datetime.now(UTC),
    )
