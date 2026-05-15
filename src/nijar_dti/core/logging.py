"""Configuración de logging estructurado.

Usa structlog para emitir logs en formato JSON en producción y formato legible
en desarrollo. Cumple con la trazabilidad exigida por ENS Medio.
"""

import logging
import sys

import structlog

from nijar_dti.config import get_settings


def configure_logging() -> None:
    """Configura el logging estructurado para toda la aplicación."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_production:
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=log_level, handlers=[logging.NullHandler()])


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Obtiene un logger estructurado."""
    return structlog.get_logger(name)
