"""Clase base para los conectores de Social Listening.

Cada conector concreto (X/Twitter, Facebook, Instagram) hereda de
``SocialListeningConnector`` e implementa ``fetch_mentions``. La clase
base define el modelo de datos común (``MentionRaw``) y la firma
asíncrona uniforme.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class SocialConnectorError(Exception):
    """Error genérico de un conector social."""


@dataclass(frozen=True)
class MentionRaw:
    """Mención bruta normalizada antes de pasar al pipeline NLP.

    Campos comunes a las tres plataformas. Cada conector rellena los que
    aplican y deja el resto en None.
    """

    fuente: str  # "twitter_x" | "facebook" | "instagram"
    fuente_id_externo: str
    autor_handle: str | None
    texto_original: str
    publicado_en: datetime
    idioma: str | None = None
    url: str | None = None
    likes: int | None = None
    compartidos: int | None = None
    comentarios: int | None = None
    alcance: int | None = None
    latitud: float | None = None
    longitud: float | None = None
    payload_original: dict[str, Any] = field(default_factory=dict)


class SocialListeningConnector(ABC):
    """Interfaz común para todos los conectores de redes sociales."""

    fuente: str  # subclase debe definirlo

    @abstractmethod
    async def fetch_mentions(self, since: datetime | None = None) -> list[MentionRaw]:
        """Devuelve las menciones nuevas posteriores a ``since``.

        Cada implementación debe ser idempotente: el filtro temporal evita
        duplicados entre poll y poll. La deduplicación final se hace
        igualmente en BBDD por ``(fuente, fuente_id_externo)``.
        """

    @property
    def is_configured(self) -> bool:
        """Indica si el conector está listo para llamar a la API real.

        Cuando es False, el scheduler ejecuta el conector solo si el modo
        ``SOCIAL_DRY_RUN`` está activo.
        """
        return True
