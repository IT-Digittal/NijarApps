"""Modelos analíticos de predicción de afluencia (A.2 / A.3).

Implementación en Python puro (sin dependencias numéricas externas, para no
introducir bloqueo tecnológico) de un modelo **estacional** transparente y
defendible, adecuado a la fuerte estacionalidad del turismo de Cabo de Gata:

- nivel base (media del histórico),
- índice estacional por mes (1-12),
- índice por día de la semana (0=lunes .. 6=domingo),
- desviación de los residuos para bandas de confianza y detección de anomalías.

`predecir(fecha) = nivel · índice_mes[mes] · índice_dow[dow]`.

Incluye validación con **MAPE** sobre *holdout* temporal y detección de
anomalías por residuo estandarizado. Funciones puras y testeables sin BBDD.

Modelos más sofisticados (ARIMA/Prophet/gradient boosting) quedan como mejora
de C.1 documentada en `docs/big-data/plan-mejora-continua.md`.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(frozen=True)
class PuntoSerie:
    """Un punto de una serie temporal diaria."""

    fecha: date
    valor: float


@dataclass
class ModeloEstacional:
    """Parámetros ajustados del modelo estacional multiplicativo."""

    nivel: float
    indice_mes: dict[int, float] = field(default_factory=dict)
    indice_dow: dict[int, float] = field(default_factory=dict)
    sigma_residuo: float = 0.0
    n_entrenamiento: int = 0

    def predecir(self, fecha: date) -> float:
        """Valor estimado para una fecha (nunca negativo)."""
        im = self.indice_mes.get(fecha.month, 1.0)
        idow = self.indice_dow.get(fecha.weekday(), 1.0)
        return max(self.nivel * im * idow, 0.0)


def _indice(valores_grupo: list[float], nivel: float) -> float:
    """Índice estacional de un grupo = media del grupo / nivel (1.0 por defecto)."""
    if not valores_grupo or nivel <= 0:
        return 1.0
    media = sum(valores_grupo) / len(valores_grupo)
    return media / nivel


def ajustar_modelo_estacional(serie: list[PuntoSerie]) -> ModeloEstacional:
    """Ajusta el modelo estacional a una serie diaria."""
    valores = [p.valor for p in serie]
    if not valores:
        return ModeloEstacional(nivel=0.0)

    nivel = sum(valores) / len(valores)

    por_mes: dict[int, list[float]] = {}
    por_dow: dict[int, list[float]] = {}
    for p in serie:
        por_mes.setdefault(p.fecha.month, []).append(p.valor)
        por_dow.setdefault(p.fecha.weekday(), []).append(p.valor)

    indice_mes = {m: _indice(v, nivel) for m, v in por_mes.items()}
    indice_dow = {d: _indice(v, nivel) for d, v in por_dow.items()}

    modelo = ModeloEstacional(
        nivel=nivel,
        indice_mes=indice_mes,
        indice_dow=indice_dow,
        n_entrenamiento=len(serie),
    )

    # Residuos in-sample para banda de confianza y umbral de anomalía
    residuos = [p.valor - modelo.predecir(p.fecha) for p in serie]
    if len(residuos) >= 2:
        modelo.sigma_residuo = statistics.pstdev(residuos)
    return modelo


def prever_serie(
    modelo: ModeloEstacional, desde: date, horizonte_dias: int
) -> list[PuntoSerie]:
    """Genera la predicción para los próximos ``horizonte_dias`` desde ``desde``."""
    salida: list[PuntoSerie] = []
    for i in range(horizonte_dias):
        fecha = desde + timedelta(days=i)
        salida.append(PuntoSerie(fecha=fecha, valor=round(modelo.predecir(fecha), 2)))
    return salida


def mape(reales: list[float], predichos: list[float]) -> float | None:
    """Mean Absolute Percentage Error (%), ignorando puntos con real == 0.

    En series turísticas con valles a cero el MAPE clásico es inestable, por
    lo que se calcula solo sobre los puntos con valor real positivo. Devuelve
    None si no hay ningún punto evaluable.
    """
    pares = [(r, p) for r, p in zip(reales, predichos, strict=False) if r > 0]
    if not pares:
        return None
    errores = [abs(r - p) / r for r, p in pares]
    return round(sum(errores) * 100 / len(errores), 2)


@dataclass
class ResultadoValidacion:
    """Resultado de la validación con holdout temporal."""

    mape: float | None
    n_test: int
    n_evaluable: int
    dias_holdout: int
    umbral: float
    cumple_umbral: bool


def validar_holdout(
    serie: list[PuntoSerie], dias_test: int = 14, umbral_mape: float = 20.0
) -> ResultadoValidacion:
    """Valida el modelo reservando los últimos ``dias_test`` como test.

    Ajusta el modelo solo con el tramo de entrenamiento y mide el MAPE sobre
    el tramo reservado, evitando fuga de información.
    """
    if len(serie) <= dias_test + 1:
        return ResultadoValidacion(
            mape=None, n_test=0, n_evaluable=0, dias_holdout=dias_test,
            umbral=umbral_mape, cumple_umbral=False,
        )

    train = serie[:-dias_test]
    test = serie[-dias_test:]
    modelo = ajustar_modelo_estacional(train)

    reales = [p.valor for p in test]
    predichos = [modelo.predecir(p.fecha) for p in test]
    valor_mape = mape(reales, predichos)
    n_evaluable = sum(1 for r in reales if r > 0)

    return ResultadoValidacion(
        mape=valor_mape,
        n_test=len(test),
        n_evaluable=n_evaluable,
        dias_holdout=dias_test,
        umbral=umbral_mape,
        cumple_umbral=(valor_mape is not None and valor_mape <= umbral_mape),
    )


@dataclass(frozen=True)
class Anomalia:
    """Punto de la serie marcado como anómalo."""

    fecha: date
    valor: float
    valor_esperado: float
    desviacion_sigmas: float


def detectar_anomalias(
    serie: list[PuntoSerie],
    modelo: ModeloEstacional | None = None,
    z: float = 3.0,
) -> list[Anomalia]:
    """Detecta anomalías como residuos que superan ``z`` desviaciones típicas.

    Útil para la detección de comportamientos atípicos de afluencia o de
    sensores (A.2). Si no se pasa modelo, se ajusta sobre la propia serie.
    """
    if modelo is None:
        modelo = ajustar_modelo_estacional(serie)
    if modelo.sigma_residuo <= 0:
        return []

    anomalias: list[Anomalia] = []
    for p in serie:
        esperado = modelo.predecir(p.fecha)
        sigmas = (p.valor - esperado) / modelo.sigma_residuo
        if abs(sigmas) >= z:
            anomalias.append(
                Anomalia(
                    fecha=p.fecha,
                    valor=p.valor,
                    valor_esperado=round(esperado, 2),
                    desviacion_sigmas=round(sigmas, 2),
                )
            )
    return anomalias


def rellenar_dias(
    conteos: dict[date, float], desde: date, hasta: date
) -> list[PuntoSerie]:
    """Construye una serie diaria continua rellenando con 0 los días sin dato.

    Imprescindible para que la estacionalidad y la predicción no se sesguen
    al ignorar los días de baja afluencia (que sí existen, con valor 0).
    """
    serie: list[PuntoSerie] = []
    dia = desde
    while dia <= hasta:
        serie.append(PuntoSerie(fecha=dia, valor=float(conteos.get(dia, 0.0))))
        dia += timedelta(days=1)
    return serie
