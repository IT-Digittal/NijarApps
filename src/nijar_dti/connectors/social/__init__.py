"""Conectores de Social Listening: X/Twitter, Facebook, Instagram."""

from nijar_dti.connectors.social.base import (
    MentionRaw,
    SocialConnectorError,
    SocialListeningConnector,
)

__all__ = [
    "MentionRaw",
    "SocialConnectorError",
    "SocialListeningConnector",
]
