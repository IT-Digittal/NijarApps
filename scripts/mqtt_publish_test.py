#!/usr/bin/env python3
"""Publica observaciones sintéticas al broker MQTT para validar la ingesta.

Uso::

    python scripts/mqtt_publish_test.py
    python scripts/mqtt_publish_test.py --count 10 --interval 2

Requiere ``paho-mqtt``. Útil para demostrar end-to-end el subscriber sin
necesidad de sensores físicos.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


SENSORES_DEMO = [
    ("smartoffice-01", "co2", 400, 1500, "ppm"),
    ("smartoffice-01", "temp", 18, 28, "°C"),
    ("smartoffice-01", "hum", 35, 75, "%"),
    ("smartoffice-01", "noise", 35, 70, "dB"),
    ("totem-rodalquilar", "aforo", 0, 50, "personas"),
    ("totem-albaricoques", "aforo", 0, 50, "personas"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("MQTT_BROKER_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_BROKER_PORT", "1883")))
    parser.add_argument("--count", type=int, default=6, help="Mensajes a publicar")
    parser.add_argument("--interval", type=float, default=1.0, help="Segundos entre mensajes")
    args = parser.parse_args()

    client = mqtt.Client(client_id="nijar-test-publisher")
    client.connect(args.host, args.port, keepalive=30)

    print(f"Conectado a MQTT {args.host}:{args.port}")
    for i in range(args.count):
        slug, measurement, lo, hi, unit = SENSORES_DEMO[i % len(SENSORES_DEMO)]
        topic = f"nijar/sensors/{slug}/{measurement}"
        payload = {
            "valor": round(random.uniform(lo, hi), 2),
            "unidades": unit,
            "observado_en": datetime.now(timezone.utc).isoformat(),
        }
        client.publish(topic, json.dumps(payload), qos=1)
        print(f"→ {topic}  {payload}")
        time.sleep(args.interval)

    client.disconnect()
    print("Hecho.")


if __name__ == "__main__":
    main()
