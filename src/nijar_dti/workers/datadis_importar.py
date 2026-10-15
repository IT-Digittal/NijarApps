"""Importa ficheros descargados de datadis.es → Datos públicos → Consultas.

Alternativa por consola a «Importar fichero» de la sección «Consumo del
municipio» del panel (vertical de Energía). Idempotente.

Uso (en producción):
    docker exec -i nijar-dti-api python -m nijar_dti.workers.datadis_importar - < julio.csv
    docker cp julio.xlsx nijar-dti-api:/tmp/ && \\
        docker exec nijar-dti-api python -m nijar_dti.workers.datadis_importar /tmp/julio.xlsx
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from nijar_dti.connectors.datadis_fichero import leer_fichero
from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging
from nijar_dti.services.datadis_service import guardar_registros


async def importar(rutas: list[str]) -> int:
    async with AsyncSessionLocal() as db:
        for ruta in rutas:
            if ruta == "-":
                contenido, nombre = sys.stdin.buffer.read(), "stdin"
            else:
                contenido, nombre = Path(ruta).read_bytes(), ruta
            registros = leer_fichero(contenido, nombre)
            cuenta = await guardar_registros(db, registros)
            fechas = [r.fecha for r in registros if r is not None]
            rango = f"{min(fechas)} → {max(fechas)}" if fechas else "sin fechas"
            print(f"{nombre}: {rango} · " + json.dumps(cuenta, ensure_ascii=False))
        await db.commit()
    print("Guardado.")
    return 0


def main() -> None:
    configure_logging()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(asyncio.run(importar(sys.argv[1:])))


if __name__ == "__main__":
    main()
