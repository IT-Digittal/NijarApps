"""Esquemas de los modelos predictivos de afluencia (A.2 / A.3)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PrediccionPunto(BaseModel):
    fecha: date
    valor_estimado: float
    banda_inferior: float = 0.0
    banda_superior: float = 0.0


class PrediccionAfluencia(BaseModel):
    metrica: str
    horizonte_dias: int
    dias_historico: int
    generado_en: datetime
    modelo: str = "estacional_multiplicativo"
    mape_validacion: float | None = None
    cumple_umbral_mape: bool = False
    puntos: list[PrediccionPunto] = Field(default_factory=list)


class ValidacionModelo(BaseModel):
    metrica: str
    modelo: str = "estacional_multiplicativo"
    mape: float | None = None
    umbral: float = 20.0
    cumple_umbral: bool = False
    n_test: int = 0
    n_evaluable: int = 0
    dias_holdout: int = 14
    metodo: str = "holdout_temporal"
    nota: str = (
        "MAPE calculado solo sobre días con afluencia real > 0 (los valles a "
        "cero hacen inestable el MAPE clásico). Ver "
        "docs/big-data/metodologia-y-limitaciones.md"
    )


class AnomaliaPunto(BaseModel):
    fecha: date
    valor: float
    valor_esperado: float
    desviacion_sigmas: float


class DeteccionAnomalias(BaseModel):
    metrica: str
    desde: date | None = None
    hasta: date | None = None
    umbral_sigmas: float = 3.0
    total_evaluado: int = 0
    anomalias: list[AnomaliaPunto] = Field(default_factory=list)
