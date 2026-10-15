"""Carga manual de Datadis (la automática corre a diario dentro de la API).

Uso (en producción, dentro del contenedor de la API):

    python -m nijar_dti.workers.datadis_carga                    # ventana por defecto
    python -m nijar_dti.workers.datadis_carga --solo publico --desde 2025-01-01
    python -m nijar_dti.workers.datadis_carga --solo privado --mes-desde 2026/01
    python -m nijar_dti.workers.datadis_carga --dry-run          # consulta sin guardar

Ventana por defecto: datos públicos del mes en curso hasta ayer (y del mes
anterior en los 5 primeros días); curva privada del mes en curso (y anterior).
Ojo: Datadis rechaza repetir la misma consulta privada durante 24 h.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging
from nijar_dti.services.datadis_service import MADRID, ejecutar_carga


async def ejecutar(a: argparse.Namespace) -> int:
    hasta = date.fromisoformat(a.hasta) if a.hasta else None
    desde = date.fromisoformat(a.desde) if a.desde else None
    mes_hasta = a.mes_hasta or (datetime.now(MADRID).strftime("%Y/%m") if a.mes_desde else None)
    async with AsyncSessionLocal() as db:
        resultado = await ejecutar_carga(
            db,
            publico_desde=desde,
            publico_hasta=hasta,
            mes_desde=a.mes_desde,
            mes_hasta=mes_hasta,
            solo=a.solo,
        )
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
        if a.dry_run:
            await db.rollback()
            print("Dry-run: no se ha guardado nada.")
        else:
            await db.commit()
            print("Guardado.")
    fallo = any("error" in (v or {}) for v in resultado.values() if isinstance(v, dict))
    return 1 if fallo else 0


def main() -> None:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--solo", choices=["publico", "privado"], default=None)
    p.add_argument("--desde", help="datos públicos desde AAAA-MM-DD (histórico)")
    p.add_argument("--hasta", help="datos públicos hasta AAAA-MM-DD (por defecto, ayer)")
    p.add_argument("--mes-desde", help="curva privada desde AAAA/MM")
    p.add_argument("--mes-hasta", help="curva privada hasta AAAA/MM (por defecto, mes actual)")
    p.add_argument("--dry-run", action="store_true")
    sys.exit(asyncio.run(ejecutar(p.parse_args())))


if __name__ == "__main__":
    main()
