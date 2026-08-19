"""Conector Social Listening para Instagram — Hashtag Search API.

Usa el endpoint ``GET /{ig-hashtag-id}/recent_media`` con la cuenta
business asociada al Ayuntamiento. Documentación oficial:
https://developers.facebook.com/docs/instagram-api/guides/hashtag-search

Cobertura:

- Hashtags configurables vía ``INSTAGRAM_HASHTAGS`` (lista separada por
  comas; por defecto ``cabodegata,nijar,playamonsul``).
- Para cada hashtag se descargan los últimos posts y se devuelven como
  ``MentionRaw``.
- En modo dry-run usa el mismo formato sintético que los demás conectores.
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


class InstagramConnector(SocialListeningConnector):
    fuente = "instagram"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.facebook_access_token and self.settings.instagram_business_account_id
        )

    @property
    def hashtags(self) -> list[str]:
        return [
            h.strip().lstrip("#") for h in self.settings.instagram_hashtags.split(",") if h.strip()
        ]

    async def fetch_mentions(self, since: datetime | None = None) -> list[MentionRaw]:
        if self.settings.social_dry_run:
            return _menciones_sinteticas_instagram(since, self.hashtags)

        if not self.is_configured:
            raise SocialConnectorError(
                "FACEBOOK_ACCESS_TOKEN o INSTAGRAM_BUSINESS_ACCOUNT_ID no configurados"
            )

        out: list[MentionRaw] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for tag in self.hashtags:
                hashtag_id = await self._resolve_hashtag_id(client, tag)
                if not hashtag_id:
                    continue
                resp = await client.get(
                    f"{_GRAPH_API_BASE}/{hashtag_id}/recent_media",
                    params={
                        "user_id": self.settings.instagram_business_account_id,
                        "fields": "id,caption,permalink,timestamp,like_count,comments_count,media_type",
                        "access_token": self.settings.facebook_access_token,
                    },
                )
                if resp.status_code >= 400:
                    log.warning(
                        "Instagram hashtag '%s' error %s: %s",
                        tag,
                        resp.status_code,
                        resp.text[:200],
                    )
                    continue
                out.extend(_parse_instagram_response(resp.json(), tag, since))
        return out

    async def _resolve_hashtag_id(self, client: httpx.AsyncClient, hashtag: str) -> str | None:
        resp = await client.get(
            f"{_GRAPH_API_BASE}/ig_hashtag_search",
            params={
                "user_id": self.settings.instagram_business_account_id,
                "q": hashtag,
                "access_token": self.settings.facebook_access_token,
            },
        )
        if resp.status_code >= 400:
            log.warning("Hashtag search '%s' error %s", hashtag, resp.status_code)
            return None
        items = resp.json().get("data", []) or []
        if items and "id" in items[0]:
            return items[0]["id"]
        return None


def _parse_instagram_response(data: dict, hashtag: str, since: datetime | None) -> list[MentionRaw]:
    posts = data.get("data", []) or []
    out: list[MentionRaw] = []
    for post in posts:
        caption = post.get("caption")
        if not caption:
            continue
        try:
            publicado_en = datetime.fromisoformat(post.get("timestamp", "").replace("Z", "+00:00"))
        except (TypeError, ValueError):
            publicado_en = datetime.now(UTC)

        if since is not None and publicado_en < since:
            continue

        out.append(
            MentionRaw(
                fuente="instagram",
                fuente_id_externo=str(post.get("id")),
                autor_handle=None,  # Instagram no expone autor en hashtag search
                texto_original=caption,
                publicado_en=publicado_en,
                idioma=None,
                url=post.get("permalink"),
                likes=post.get("like_count"),
                comentarios=post.get("comments_count"),
                payload_original={**post, "hashtag": hashtag},
            )
        )
    return out


def _menciones_sinteticas_instagram(
    since: datetime | None, hashtags: list[str]
) -> list[MentionRaw]:
    base = since or (datetime.now(UTC) - timedelta(hours=3))
    plantilla = [
        (
            "¡Atardecer mágico en la #PlayaDeMonsul! No me canso de venir 🌅 #cabodegata #nijar",
            542,
            28,
        ),
        ("Day trip to #cabodegata Natural Park — wow! Stunning landscapes everywhere.", 312, 19),
        ("Endlich wieder am Strand von #PlayaMonsul! Wir kommen jedes Jahr zurück.", 198, 11),
        ("Vue magnifique depuis le belvédère de l'Amatista. À ne pas rater à #nijar.", 167, 8),
    ]
    out: list[MentionRaw] = []
    tag = hashtags[0] if hashtags else "cabodegata"
    for i, (caption, likes, comments) in enumerate(plantilla):
        out.append(
            MentionRaw(
                fuente="instagram",
                fuente_id_externo=f"ig-dryrun-{int(base.timestamp())}-{i}",
                autor_handle=None,
                texto_original=caption,
                publicado_en=base + timedelta(minutes=i * 13),
                idioma=None,
                url=None,
                likes=likes,
                comentarios=comments,
                payload_original={"dry_run": True, "hashtag": tag},
            )
        )
    return out
