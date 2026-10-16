#!/usr/bin/env python3
"""Verificador de las ortofotos históricas del Gemelo vivo 2D.

Comprueba en vivo, desde el servidor, qué vuelos aparecerán en el selector
«Ortofoto histórica»:

1. **IGN** (PNOA histórico): vuelos con imagen sobre Níjar.
2. **Junta de Andalucía** (REDIAM e IECA): para cada vuelo, qué URL responde,
   qué capa se ha elegido de su GetCapabilities y si hay imagen sobre Níjar
   en EPSG:3857 (lo que pide el mapa). Los que fallan no se muestran.

Solo lectura. Uso (en producción):
    docker exec -i nijar-dti-api python - < scripts/verificar_ortofotos.py
"""

from __future__ import annotations

import asyncio

import httpx

from nijar_dti.services import ortofotos_service as svc

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"


async def main() -> None:
    print("\nIGN · PNOA histórico")
    try:
        url, capas, verificada = await svc.listar_ortofotos()
        print(f"  {OK}  {url} · {len(capas)} vuelos" + ("" if verificada else " (sin verificar)"))
        print("     " + ", ".join(c.etiqueta for c in capas))
    except httpx.HTTPError as exc:
        print(f"  {FAIL}  IGN no disponible: {exc}")

    print("\nJunta de Andalucía (REDIAM / IECA)")
    vuelos, diags = await svc.listar_ortofotos_junta(forzar=True)
    for d in diags:
        if d.con_imagen:
            print(f"  {OK}  {d.etiqueta:8} {d.url} · capa «{d.capa}»")
        else:
            motivo = d.error or "sin respuesta"
            print(f"  {FAIL}  {d.etiqueta:8} {d.url} · {motivo}")
            if d.capas_disponibles:
                print(f"           capas: {', '.join(d.capas_disponibles[:12])}")
    print(f"\n{len(vuelos)} de {len(diags)} vuelos de la Junta aparecerán en el selector.\n")


if __name__ == "__main__":
    asyncio.run(main())
