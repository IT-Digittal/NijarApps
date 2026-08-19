"""Conector Social Listening para X (Twitter) — API v2 Recent Search.

Documentación: https://developer.x.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent

Funcionamiento:

1. Construye una query con los términos clave de Níjar / Cabo de Gata.
2. Llama al endpoint ``GET /2/tweets/search/recent`` filtrando por
   ``start_time`` (siempre que se conozca el timestamp del último poll).
3. Solicita campos extendidos: autor, métricas públicas, geolocalización,
   idioma detectado.
4. Devuelve la lista de menciones normalizadas a ``MentionRaw``.

En modo ``dry_run`` no llama a la API; devuelve menciones sintéticas para
desarrollo y demos.
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

_TWITTER_API_BASE = "https://api.x.com/2"
_TWEET_FIELDS = "id,text,created_at,lang,author_id,public_metrics,geo"
_USER_FIELDS = "username,name"
_EXPANSIONS = "author_id"


class TwitterConnector(SocialListeningConnector):
    """Conector Recent Search v2 de X (antes Twitter)."""

    fuente = "twitter_x"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.twitter_bearer_token)

    async def fetch_mentions(self, since: datetime | None = None) -> list[MentionRaw]:
        if self.settings.social_dry_run:
            return _menciones_sinteticas_x(since)

        if not self.is_configured:
            raise SocialConnectorError("TWITTER_BEARER_TOKEN no configurado")

        params: dict[str, str | int] = {
            "query": self.settings.twitter_search_query,
            "max_results": min(max(self.settings.twitter_max_results_per_poll, 10), 100),
            "tweet.fields": _TWEET_FIELDS,
            "user.fields": _USER_FIELDS,
            "expansions": _EXPANSIONS,
        }
        if since is not None:
            # X exige ISO 8601 con Z (UTC)
            params["start_time"] = since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        headers = {"Authorization": f"Bearer {self.settings.twitter_bearer_token}"}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_TWITTER_API_BASE}/tweets/search/recent",
                params=params,
                headers=headers,
            )
        if resp.status_code == 429:
            raise SocialConnectorError("Rate limit X excedido")
        if resp.status_code >= 400:
            raise SocialConnectorError(f"X API error {resp.status_code}: {resp.text[:200]}")
        return _parse_twitter_response(resp.json())


def _parse_twitter_response(data: dict) -> list[MentionRaw]:
    tweets = data.get("data", []) or []
    users_index = {u["id"]: u for u in (data.get("includes", {}) or {}).get("users", []) or []}
    out: list[MentionRaw] = []
    for tw in tweets:
        author = users_index.get(tw.get("author_id"), {}) if tw.get("author_id") else {}
        metrics = tw.get("public_metrics", {}) or {}
        geo = tw.get("geo", {}) or {}
        coords = geo.get("coordinates", {}).get("coordinates") if isinstance(geo, dict) else None
        lat = lon = None
        if isinstance(coords, list) and len(coords) == 2:
            # GeoJSON: [lon, lat]
            lon, lat = float(coords[0]), float(coords[1])

        try:
            publicado_en = datetime.fromisoformat(tw.get("created_at", "").replace("Z", "+00:00"))
        except (TypeError, ValueError):
            publicado_en = datetime.now(UTC)

        out.append(
            MentionRaw(
                fuente="twitter_x",
                fuente_id_externo=str(tw.get("id")),
                autor_handle=("@" + author["username"]) if author.get("username") else None,
                texto_original=tw.get("text", ""),
                publicado_en=publicado_en,
                idioma=tw.get("lang"),
                url=(
                    f"https://x.com/{author.get('username')}/status/{tw.get('id')}"
                    if author.get("username") and tw.get("id")
                    else None
                ),
                likes=metrics.get("like_count"),
                compartidos=metrics.get("retweet_count"),
                comentarios=metrics.get("reply_count"),
                alcance=metrics.get("impression_count"),
                latitud=lat,
                longitud=lon,
                payload_original=tw,
            )
        )
    return out


def _menciones_sinteticas_x(since: datetime | None) -> list[MentionRaw]:
    """Genera menciones de ejemplo realistas para modo dry-run."""
    base = since or (datetime.now(UTC) - timedelta(hours=1))
    plantilla = [
        (
            "@viajero_anonimo",
            "El atardecer en la Playa de Mónsul es algo único. Cabo de Gata sigue siendo mágico. #Níjar #CaboDeGata",
            "es",
            142,
            18,
            7,
        ),
        (
            "@traveler_eu",
            "Best beach in Spain hands down — Mónsul Beach in Cabo de Gata. Worth the drive!",
            "en",
            86,
            12,
            4,
        ),
        (
            "@nature_lover_de",
            "Wahnsinnige Landschaft im Naturpark Cabo de Gata-Níjar. Ein absolutes Highlight!",
            "de",
            53,
            6,
            2,
        ),
        (
            "@famille_voyage",
            "Vacances incroyables à Níjar, on recommande le centre des visiteurs Las Amoladeras.",
            "fr",
            31,
            4,
            1,
        ),
    ]
    out: list[MentionRaw] = []
    for i, (autor, texto, lang, likes, rt, reply) in enumerate(plantilla):
        out.append(
            MentionRaw(
                fuente="twitter_x",
                fuente_id_externo=f"dryrun-{int(base.timestamp())}-{i}",
                autor_handle=autor,
                texto_original=texto,
                publicado_en=base + timedelta(minutes=i * 7),
                idioma=lang,
                url=None,
                likes=likes,
                compartidos=rt,
                comentarios=reply,
                alcance=likes * 30,
                payload_original={"dry_run": True},
            )
        )
    return out
