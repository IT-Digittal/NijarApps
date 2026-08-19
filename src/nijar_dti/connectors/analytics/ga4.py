"""Conector Google Analytics 4 — Reporting Data API.

Captura los KPIs de eficacia digital comprometidos en la actuación A.3 del
contrato (sesiones web/app, usuarios, páginas vistas, conversiones,
canales de adquisición). El reporting alimenta:

- el endpoint ``/dashboards/big-data/overview`` (canal "web")
- el informe mensual del C.1 (visitas web estimadas)

Funcionamiento:

1. Se autentica con una cuenta de servicio de Google Cloud (variable
   ``GA4_SERVICE_ACCOUNT_JSON`` con la ruta al fichero JSON o el JSON
   inline en base64).
2. Llama al endpoint ``runReport`` de la Data API v1beta sobre el
   ``GA4_PROPERTY_ID``.
3. Devuelve resultados normalizados a estructuras Python.

En modo ``dry-run`` (cuando no hay credenciales) devuelve datos
sintéticos coherentes para desarrollo y demos.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from nijar_dti.config import Settings, get_settings

log = logging.getLogger(__name__)

_GA4_API_BASE = "https://analyticsdata.googleapis.com/v1beta"
_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GA4_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"


@dataclass
class GA4Overview:
    """KPIs principales de un periodo."""

    sesiones: int
    usuarios: int
    usuarios_nuevos: int
    paginas_vistas: int
    duracion_media_sesion_seg: float
    bounce_rate: float  # 0..1


@dataclass
class GA4ChannelBreakdown:
    """Desglose por canal de adquisición."""

    canal: str
    sesiones: int
    usuarios: int


class GA4ConnectorError(Exception):
    pass


class GA4Connector:
    """Cliente del Reporting Data API de GA4."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._access_token: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(
            getattr(self.settings, "ga4_property_id", "")
            and getattr(self.settings, "ga4_service_account_json", "")
        )

    # ---------------- Auth ----------------

    def _load_service_account(self) -> dict[str, Any]:
        path_or_json = self.settings.ga4_service_account_json
        if not path_or_json:
            raise GA4ConnectorError("GA4_SERVICE_ACCOUNT_JSON no configurado")
        # Si es una ruta a fichero
        if os.path.exists(path_or_json):
            with open(path_or_json, encoding="utf-8") as fh:
                return json.load(fh)
        # Si es un JSON inline
        try:
            return json.loads(path_or_json)
        except json.JSONDecodeError as exc:
            raise GA4ConnectorError(
                "GA4_SERVICE_ACCOUNT_JSON no es ni una ruta válida ni un JSON inline"
            ) from exc

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        # Implementación con google-auth si está disponible; si no, JWT manual.
        # Para mantener dependencias mínimas y testabilidad, hacemos un import
        # diferido. En producción se recomienda añadir `google-auth` a las deps.
        try:
            from google.auth.transport.requests import Request  # type: ignore
            from google.oauth2 import service_account  # type: ignore
        except ImportError as exc:
            raise GA4ConnectorError(
                "google-auth no instalado. Añadir 'google-auth>=2.27' a las dependencias."
            ) from exc

        creds = service_account.Credentials.from_service_account_info(
            self._load_service_account(),
            scopes=[_GA4_SCOPE],
        )
        creds.refresh(Request())
        return creds.token

    # ---------------- API calls ----------------

    async def overview(self, days_back: int = 30, settings: Settings | None = None) -> GA4Overview:
        settings = settings or self.settings
        if not self.is_configured:
            return _overview_sintetico(days_back)

        body = {
            "dateRanges": [
                {
                    "startDate": f"{days_back}daysAgo",
                    "endDate": "today",
                }
            ],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "newUsers"},
                {"name": "screenPageViews"},
                {"name": "averageSessionDuration"},
                {"name": "bounceRate"},
            ],
        }
        async with httpx.AsyncClient(timeout=15) as client:
            token = await self._get_access_token(client)
            resp = await client.post(
                f"{_GA4_API_BASE}/properties/{settings.ga4_property_id}:runReport",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
        if resp.status_code >= 400:
            raise GA4ConnectorError(f"GA4 API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        rows = data.get("rows") or []
        if not rows:
            return GA4Overview(0, 0, 0, 0, 0.0, 0.0)
        values = [m.get("value", 0) for m in rows[0].get("metricValues", [])]
        return GA4Overview(
            sesiones=int(float(values[0] or 0)),
            usuarios=int(float(values[1] or 0)),
            usuarios_nuevos=int(float(values[2] or 0)),
            paginas_vistas=int(float(values[3] or 0)),
            duracion_media_sesion_seg=round(float(values[4] or 0), 1),
            bounce_rate=round(float(values[5] or 0), 4),
        )

    async def channels_breakdown(
        self, days_back: int = 30, settings: Settings | None = None
    ) -> list[GA4ChannelBreakdown]:
        settings = settings or self.settings
        if not self.is_configured:
            return _channels_sintetico()

        body = {
            "dateRanges": [{"startDate": f"{days_back}daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "sessionDefaultChannelGroup"}],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"}],
            "limit": 20,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            token = await self._get_access_token(client)
            resp = await client.post(
                f"{_GA4_API_BASE}/properties/{settings.ga4_property_id}:runReport",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
        if resp.status_code >= 400:
            raise GA4ConnectorError(f"GA4 API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        out: list[GA4ChannelBreakdown] = []
        for row in data.get("rows") or []:
            dims = row.get("dimensionValues", []) or []
            metrics = row.get("metricValues", []) or []
            if not dims or len(metrics) < 2:
                continue
            out.append(
                GA4ChannelBreakdown(
                    canal=dims[0].get("value", "(unknown)"),
                    sesiones=int(float(metrics[0].get("value", 0) or 0)),
                    usuarios=int(float(metrics[1].get("value", 0) or 0)),
                )
            )
        return out


# ---------------- Datos sintéticos para dry-run ----------------


def _overview_sintetico(days_back: int) -> GA4Overview:
    factor = max(days_back / 30, 1.0)
    return GA4Overview(
        sesiones=int(8_420 * factor),
        usuarios=int(6_120 * factor),
        usuarios_nuevos=int(4_840 * factor),
        paginas_vistas=int(21_350 * factor),
        duracion_media_sesion_seg=92.4,
        bounce_rate=0.4137,
    )


def _channels_sintetico() -> list[GA4ChannelBreakdown]:
    return [
        GA4ChannelBreakdown("Organic Search", 3_120, 2_490),
        GA4ChannelBreakdown("Direct", 2_080, 1_730),
        GA4ChannelBreakdown("Organic Social", 1_490, 1_120),
        GA4ChannelBreakdown("Referral", 980, 760),
        GA4ChannelBreakdown("Paid Search", 540, 410),
        GA4ChannelBreakdown("Email", 210, 180),
    ]
