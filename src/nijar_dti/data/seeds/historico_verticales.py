"""Histórico mensual sintético (2 años) de métricas por vertical.

Genera una serie realista por (vertical, indicador): magnitud base del último
mes × perfil estacional (municipio costero mediterráneo, pico en verano; el
alumbrado al revés, pico en invierno) × tendencia interanual. Al comparar el
mismo mes de un año a otro la estacionalidad se cancela, así que la variación
interanual ≈ la tendencia configurada (historia coherente y determinista).

Cada indicador lleva un `sentido` para que el panel lo coloree bien:
- `bajar_bueno`: consumo, coste, pérdidas, incidencias (bajar es positivo).
- `subir_bueno`: accesos/afluencia (subir es positivo).
"""

from __future__ import annotations

from datetime import date

# vertical, indicador, nombre, unidad, base (último mes), estacion, tendencia_anual, sentido
INDICADORES: list[tuple[str, str, str, str, float, str, float, str]] = [
    ("energia", "consumo_kwh", "Consumo energético", "kWh", 900000, "verano", -0.04, "bajar_bueno"),
    ("energia", "coste_eur", "Coste / facturación", "€", 148000, "verano", 0.06, "bajar_bueno"),
    ("alumbrado", "consumo_kwh", "Consumo de alumbrado", "kWh", 112000, "invierno", -0.12, "bajar_bueno"),
    ("agua", "consumo_m3", "Consumo de agua", "m³", 210000, "verano", -0.02, "bajar_bueno"),
    ("agua", "perdidas_m3", "Pérdidas de agua", "m³", 38000, "verano", -0.08, "bajar_bueno"),
    ("residuos", "toneladas", "Residuos recogidos", "t", 1450, "verano", 0.03, "bajar_bueno"),
    ("movilidad", "accesos", "Accesos al municipio", "veh", 96000, "verano", 0.05, "subir_bueno"),
    ("seguridad", "incidencias", "Incidencias de seguridad", "nº", 42, "verano", -0.06, "bajar_bueno"),
]

# Perfiles estacionales normalizados (media ≈ 1), por mes Ene..Dic.
_ESTACION: dict[str, list[float]] = {
    "verano": [0.85, 0.85, 0.90, 0.96, 1.06, 1.20, 1.35, 1.34, 1.14, 0.98, 0.86, 0.81],
    "invierno": [1.18, 1.12, 1.00, 0.90, 0.80, 0.74, 0.72, 0.78, 0.90, 1.02, 1.14, 1.20],
}


def _periodos(anios: int) -> list[str]:
    """Últimos `anios*12` meses cerrados (hasta el mes anterior), de antiguo a reciente."""
    hoy = date.today()
    y, m = hoy.year, hoy.month - 1
    if m == 0:
        y, m = y - 1, 12
    periodos: list[str] = []
    for _ in range(anios * 12):
        periodos.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(periodos))


def generar_historico_seed(anios: int = 2) -> list[dict[str, object]]:
    """Devuelve las filas de histórico a insertar."""
    periodos = _periodos(anios)
    n = len(periodos)
    filas: list[dict[str, object]] = []
    for vertical, indicador, _nombre, unidad, base, estacion, trend, _sentido in INDICADORES:
        est = _ESTACION[estacion]
        for i, periodo in enumerate(periodos):
            mes = int(periodo[5:7])
            meses_atras = (n - 1) - i
            factor_tendencia = (1.0 + trend) ** (-meses_atras / 12.0)
            valor = base * est[mes - 1] * factor_tendencia
            valor = round(valor) if unidad == "nº" else round(valor, 2)
            filas.append({
                "vertical": vertical,
                "indicador": indicador,
                "periodo": periodo,
                "valor": float(valor),
                "unidad": unidad,
            })
    return filas
