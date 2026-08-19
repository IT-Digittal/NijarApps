#!/usr/bin/env python3
"""Verificador de la meteorología pública (Open-Meteo).

Comprueba que la plataforma obtiene las condiciones actuales y la previsión de
Open-Meteo para las coordenadas configuradas. No requiere credenciales.

Uso:
    python -m scripts.verificar_openmeteo
    python scripts/verificar_openmeteo.py
"""

from __future__ import annotations

import asyncio
import sys

from nijar_dti.config import get_settings
from nijar_dti.connectors.openmeteo import ClienteOpenMeteo, OpenMeteoError

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"


async def _run() -> int:
    s = get_settings()
    print("\n== Verificación de meteorología pública (Open-Meteo) ==\n")
    cli = ClienteOpenMeteo(s.openmeteo_base_url, s.openmeteo_timeout_seconds)
    try:
        m = await cli.actual(s.openmeteo_latitud, s.openmeteo_longitud, s.openmeteo_dias_prevision)
    except OpenMeteoError as e:
        print(f"  {FAIL}  No se pudo obtener el tiempo  —  {e}")
        print("\nResultado: FALLA.\n")
        return 1

    print(f"  {OK}  Condiciones actuales  —  "
          f"{m['temperatura_c']}°C, {m['descripcion']}, humedad {m['humedad_pct']}% "
          f"(lat {m['latitud']}, lon {m['longitud']})")
    prev = m.get("prevision") or []
    if prev:
        d = prev[0]
        print(f"  {OK}  Previsión disponible  —  {len(prev)} días; hoy {d['descripcion']} "
              f"{d['temp_min_c']}–{d['temp_max_c']}°C")
    else:
        print(f"  {FAIL}  Sin previsión diaria")
        return 1
    print("\nResultado: TODO OK. La meteorología pública se integra correctamente.\n")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
