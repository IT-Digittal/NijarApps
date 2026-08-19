"""Conector Social Listening para Facebook — Graph API.

Captura los posts publicados en la página oficial del Ayuntamiento y los
comentarios recientes (menciones implícitas del destino). Los posts del
propio Ayuntamiento se etiquetan como ``encuesta_municipal`` en el motor
analítico para diferenciarlos de menciones externas.

Documentación: https://developers.facebook.com/docs/graph-api/reference/page/feed
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.social.base import (
    MentionRaw,
    SocialConnectorError,
    SocialListeningConnector,
)

log = logging.getLogger(__name__)

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class FacebookConnector(SocialListeningConnector):
    fuente = "facebook"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _page_ref(self) -> str:
        """ID numérico de la página o, en su defecto, el alias público."""
        return self.settings.facebook_page_id or self.settings.facebook_page_handle

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.facebook_access_token and self._page_ref)

    async def fetch_mentions(self, since: datetime | None = None) -> list[MentionRaw]:
        if self.settings.social_dry_run:
            return _menciones_sinteticas_facebook(since)

        if not self.is_configured:
            raise SocialConnectorError(
                "FACEBOOK_ACCESS_TOKEN o FACEBOOK_PAGE_ID/HANDLE no configurados"
            )

        params: dict[str, str | int] = {
            "access_token": self.settings.facebook_access_token,
            "fields": (
                "id,message,created_time,permalink_url,reactions.summary(true)"
                ",comments.summary(true),shares,from"
            ),
            "limit": 100,
        }
        if since is not None:
            params["since"] = int(since.astimezone(UTC).timestamp())

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_GRAPH_API_BASE}/{self._page_ref}/feed",
                params=params,
            )
        if resp.status_code >= 400:
            raise SocialConnectorError(
                f"Facebook Graph API error {resp.status_code}: {resp.text[:200]}"
            )
        return _parse_facebook_response(resp.json())


def _parse_facebook_response(data: dict) -> list[MentionRaw]:
    posts = data.get("data", []) or []
    out: list[MentionRaw] = []
    for post in posts:
        mensaje = post.get("message")
        if not mensaje:
            continue
        try:
            publicado_en = datetime.fromisoformat(
                post.get("created_time", "").replace("Z", "+00:00")
            )
        except (TypeError, ValueError):
            publicado_en = datetime.now(UTC)
        reacciones = (post.get("reactions") or {}).get("summary", {}).get("total_count")
        comentarios = (post.get("comments") or {}).get("summary", {}).get("total_count")
        shares = (post.get("shares") or {}).get("count")
        autor = (post.get("from") or {}).get("name")

        out.append(
            MentionRaw(
                fuente="facebook",
                fuente_id_externo=str(post.get("id")),
                autor_handle=autor,
                texto_original=mensaje,
                publicado_en=publicado_en,
                idioma=None,
                url=post.get("permalink_url"),
                likes=reacciones,
                compartidos=shares,
                comentarios=comentarios,
                payload_original=post,
            )
        )
    return out


def _menciones_sinteticas_facebook(since: datetime | None) -> list[MentionRaw]:
    base = since or (datetime.now(UTC) - timedelta(hours=2))
    plantilla = [
        (
            "Ayuntamiento de Níjar",
            "Recordamos que el aforo de la playa de Mónsul es limitado durante los meses de julio y agosto. Reserva tu acceso en la web municipal.",
            234,
            45,
            56,
        ),
        (
            "Visitor de Almería",
            "Acabamos de pasar el fin de semana en San José y volveremos seguro. Las playas son una pasada y la gente súper amable.",
            89,
            6,
            12,
        ),
        (
            "Comercio Níjar",
            "Ya tenemos las nuevas jarapas hechas a mano para la temporada. ¡Os esperamos en el casco histórico!",
            67,
            8,
            4,
        ),
    ]
    out: list[MentionRaw] = []
    for i, (autor, mensaje, likes, shares, comments) in enumerate(plantilla):
        out.append(
            MentionRaw(
                fuente="facebook",
                fuente_id_externo=f"fb-dryrun-{int(base.timestamp())}-{i}",
                autor_handle=autor,
                texto_original=mensaje,
                publicado_en=base + timedelta(minutes=i * 11),
                idioma="es",
                url=None,
                likes=likes,
                compartidos=shares,
                comentarios=comments,
                payload_original={"dry_run": True},
            )
        )
    return out
