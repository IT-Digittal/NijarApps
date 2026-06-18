"""Esquemas de los KPIs analíticos avanzados del observatorio (A.3).

Cubren dos indicadores exigidos por el Pliego que no derivan directamente
del pipeline de sentimiento:

- **Índice tipo NPS** (proxy de satisfacción) — PPT A.3.
- **Composición lingüística de visitantes** — aproximación honesta al
  origen del visitante por convergencia de señales lingüísticas.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NPSComponente(BaseModel):
    """Contribución de una señal concreta al NPS proxy."""

    señal: str
    promotores: int = 0
    pasivos: int = 0
    detractores: int = 0
    muestra: int = 0
    nps: float | None = None


class NPSProxy(BaseModel):
    """Índice tipo NPS calculado como proxy de satisfacción (A.3).

    No es un NPS de encuesta clásica ("¿recomendarías…?") sino un proxy
    construido por convergencia de señales disponibles. ``es_proxy`` lo deja
    explícito para auditoría.
    """

    desde: datetime | None = None
    hasta: datetime | None = None
    nps: float = Field(..., ge=-100, le=100)
    promotores: int = 0
    pasivos: int = 0
    detractores: int = 0
    muestra_total: int = 0
    componentes: list[NPSComponente] = Field(default_factory=list)
    es_proxy: bool = True
    metodologia: str = (
        "Proxy de satisfacción por convergencia de señales: sentimiento de "
        "menciones en RRSS/reseñas (positivo=promotor, negativo=detractor), "
        "feedback útil/no-útil del chatbot y valoraciones de encuestas "
        "municipales. NPS = %promotores − %detractores. Ver "
        "docs/big-data/metodologia-y-limitaciones.md"
    )


class IdiomaComposicion(BaseModel):
    """Peso de un idioma en la composición lingüística de visitantes."""

    idioma: str
    conteo: int
    porcentaje: float = Field(..., ge=0, le=100)
    # Banda de confianza al 95 % (puntos porcentuales) por tamaño de muestra.
    banda_confianza_pp: float = 0.0


class ComposicionLinguistica(BaseModel):
    """KPI "Composición lingüística de visitantes" (aproximación al origen).

    Cruza cuatro señales convergentes ya recogidas por la plataforma —idioma
    del tótem, de la app/web (visitas), de las interacciones del chatbot y de
    las menciones en RRSS— para estimar la mezcla de procedencias sin usar
    datos demográficos individuales. Sujeto a k-anonimato.
    """

    desde: datetime | None = None
    hasta: datetime | None = None
    muestra_total: int = 0
    idiomas: list[IdiomaComposicion] = Field(default_factory=list)
    señales_usadas: list[str] = Field(default_factory=list)
    k_anonimato: int = 0
    registros_suprimidos: int = 0
    es_aproximacion: bool = True
    metodologia: str = (
        "Convergencia de señales lingüísticas (tótem, web/app, chatbot, RRSS). "
        "Aproximación al origen, no medición censal. k-anonimato aplicado. "
        "Ver docs/big-data/metodologia-y-limitaciones.md"
    )
