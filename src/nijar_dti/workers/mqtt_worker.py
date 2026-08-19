"""Worker MQTT — proceso autónomo de ingesta IoT en tiempo real.

Ejecutar con::

    python -m nijar_dti.workers.mqtt_worker

Detiene limpiamente al recibir SIGINT/SIGTERM.
"""

from __future__ import annotations

import signal
import sys

from nijar_dti.core.logging import configure_logging, get_logger
from nijar_dti.mqtt.subscriber import MqttSubscriber


def main() -> None:
    configure_logging()
    log = get_logger(__name__)
    log.info("Arrancando worker MQTT")

    subscriber = MqttSubscriber()

    def _shutdown(signum, frame):  # noqa: ARG001
        log.info("Señal recibida, deteniendo worker MQTT", signal=signum)
        subscriber.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        subscriber.run()
    except Exception as exc:  # noqa: BLE001
        log.exception("Error fatal en worker MQTT", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
