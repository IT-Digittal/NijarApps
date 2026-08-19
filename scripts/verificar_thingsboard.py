#!/usr/bin/env python3
"""Verificador de la vertical IoT municipal (ThingsBoard): banderas y aforo.

Comprueba que la plataforma lee en tiempo real las banderas de playa y el aforo
del P.N. Cabo de Gata desde ThingsBoard. Requiere ``THINGSBOARD_BASE_URL``,
``THINGSBOARD_USUARIO`` y ``THINGSBOARD_PASSWORD``. Solo lectura.

Uso:
    python -m scripts.verificar_thingsboard
    python scripts/verificar_thingsboard.py
"""

from __future__ import annotations

import asyncio
import sys

from nijar_dti.connectors.thingsboard import ThingsBoardError
from nijar_dti.services import gemelo_service as svc

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


async def _run() -> int:
    print("\n== Verificación de la vertical IoT municipal (ThingsBoard) ==\n")
    if not svc.thingsboard_configurado():
        _linea(FAIL, "ThingsBoard sin configurar",
               "faltan THINGSBOARD_BASE_URL / USUARIO / PASSWORD")
        print("\nResultado: FALLA (configuración).\n")
        return 1
    _linea(OK, "Configuración presente")

    fallos = 0
    try:
        b = await svc.banderas_playas()
        if b.total:
            _linea(OK, "Banderas de playa accesibles", f"{b.total} banderas leídas")
        else:
            _linea(WARN, "Conecta pero no devuelve banderas", "revisa el tipo de dispositivo")
    except ThingsBoardError as e:
        _linea(FAIL, "No se pueden leer las banderas", str(e))
        fallos += 1

    try:
        a = await svc.aforo_parque()
        if a.aforo_actual is not None:
            _linea(OK, "Aforo del parque accesible", f"{a.aforo_actual} vehículos ahora")
        else:
            _linea(WARN, "Aforo sin dato actual", "el activo puede no tener telemetría reciente")
    except ThingsBoardError as e:
        _linea(FAIL, "No se puede leer el aforo", str(e))
        fallos += 1

    print()
    if fallos:
        print(f"Resultado: FALLA · {fallos} error(es).\n")
        return 1
    print("Resultado: TODO OK. La vertical IoT municipal se integra correctamente.\n")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
