"""Worker Social Listening — polling periódico de las RRSS.

Ejecutar con::

    python -m nijar_dti.workers.social_worker

Variables de entorno relevantes:

- ``SOCIAL_LISTENING_ENABLED``: si es false el worker arranca pero queda
  inactivo (útil para entornos en los que se quiere validar la imagen
  Docker pero todavía no operar).
- ``SOCIAL_DRY_RUN``: cuando es true se usan datos sintéticos en lugar
  de llamar a las APIs externas.
- ``SOCIAL_POLLING_INTERVAL_MINUTES``: cadencia entre polls.

Cuando recibe SIGINT/SIGTERM termina el bucle limpiamente al final del
poll en curso.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import UTC, datetime, timedelta

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.social.facebook import FacebookConnector
from nijar_dti.connectors.social.instagram import InstagramConnector
from nijar_dti.connectors.social.pipeline import ejecutar_poll
from nijar_dti.connectors.social.twitter import TwitterConnector
from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging, get_logger

log = logging.getLogger(__name__)


class SocialWorker:
    """Worker que ejecuta polls periódicos contra los conectores activos."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._stop = asyncio.Event()
        self._last_poll: datetime | None = None

    def request_stop(self) -> None:
        self._stop.set()

    @property
    def conectores(self):
        return [
            TwitterConnector(self.settings),
            FacebookConnector(self.settings),
            InstagramConnector(self.settings),
        ]

    async def _poll(self) -> None:
        # Primer poll: pedimos solo lo último (1h hacia atrás) para no
        # saturar las APIs ni pasar la ventana máxima de cada plataforma.
        since = self._last_poll or (datetime.now(UTC) - timedelta(hours=1))
        async with AsyncSessionLocal() as db:
            stats = await ejecutar_poll(db, self.conectores, desde=since, settings=self.settings)
        log.info(
            "Poll completado por_fuente=%s nuevas=%s duplicadas=%s",
            stats.por_fuente,
            stats.nuevas,
            stats.duplicadas,
        )
        self._last_poll = datetime.now(UTC)

    async def run(self) -> None:
        intervalo = max(self.settings.social_polling_interval_minutes, 1) * 60

        if not self.settings.social_listening_enabled:
            log.info(
                "Social Listening DESHABILITADO (SOCIAL_LISTENING_ENABLED=false). El worker queda dormido."
            )
            await self._stop.wait()
            return

        log.info(
            "Social worker arrancado. Intervalo=%d min · dry_run=%s",
            self.settings.social_polling_interval_minutes,
            self.settings.social_dry_run,
        )

        while not self._stop.is_set():
            try:
                await self._poll()
            except Exception as exc:  # noqa: BLE001
                log.exception("Error en poll Social Listening: %s", exc)

            try:
                await asyncio.wait_for(self._stop.wait(), timeout=intervalo)
            except TimeoutError:
                continue

        log.info("Social worker detenido")


def main() -> None:
    configure_logging()
    structlog_log = get_logger(__name__)
    structlog_log.info("Arrancando worker Social Listening")

    worker = SocialWorker()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _shutdown(signum, frame):  # noqa: ARG001
        structlog_log.info("Señal recibida, deteniendo worker", signal=signum)
        loop.call_soon_threadsafe(worker.request_stop)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(worker.run())
    except Exception as exc:  # noqa: BLE001
        structlog_log.exception("Error fatal en worker Social Listening", error=str(exc))
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
