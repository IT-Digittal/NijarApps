"""CLI: importa el inventario de alumbrado exportado de WeLight (Excel).

Uso:

    # Comprueba el fichero sin tocar la base de datos
    python -m nijar_dti.workers.importar_inventario_alumbrado Inventario_Nijar.xlsx --dry-run

    # Sustituye las luminarias, cuadros y zonas de demostración por el inventario real
    python -m nijar_dti.workers.importar_inventario_alumbrado Inventario_Nijar.xlsx
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from nijar_dti.services.inventario_alumbrado_service import importar, leer_inventario_welight


async def _importar(ruta: Path) -> dict:
    from nijar_dti.core.database import AsyncSessionLocal

    inv = leer_inventario_welight(ruta.read_bytes())
    async with AsyncSessionLocal() as db:
        resumen = await importar(db, inv)
        await db.commit()
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Importa el inventario WeLight de alumbrado")
    parser.add_argument("fichero", type=Path, help="Excel 'Inventory para Níjar' de WeLight")
    parser.add_argument("--dry-run", action="store_true", help="Solo lee y resume el fichero")
    args = parser.parse_args(argv)

    if args.dry_run:
        resumen = leer_inventario_welight(args.fichero.read_bytes()).resumen()
    else:
        resumen = asyncio.run(_importar(args.fichero))
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
