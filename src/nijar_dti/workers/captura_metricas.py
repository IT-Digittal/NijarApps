"""Captura manual del histórico mensual real (la automática corre a diario en la API).

Uso (en producción, dentro del contenedor de la API):

    python -m nijar_dti.workers.captura_metricas                       # último mes cerrado
    python -m nijar_dti.workers.captura_metricas --periodo 2026-09     # un mes concreto
    python -m nijar_dti.workers.captura_metricas --desde 2025-01       # rellenar hacia atrás
    python -m nijar_dti.workers.captura_metricas --estado              # qué es real y qué ejemplo
    python -m nijar_dti.workers.captura_metricas --dry-run             # calcula sin guardar

Solo se guardan meses completos de fuentes reales (hoy, la curva horaria de
Datadis); el resto del histórico sigue marcado como «ejemplo».
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging
from nijar_dti.services.metricas_historicas_service import (
    MADRID,
    capturar_mes,
    estado,
    periodo_anterior,
    periodos_entre,
)


async def ejecutar(a: argparse.Namespace) -> int:
    ultimo = periodo_anterior(datetime.now(MADRID).date())
    async with AsyncSessionLocal() as db:
        if a.estado:
            print(json.dumps(await estado(db), ensure_ascii=False, indent=2))
            return 0
        periodos = periodos_entre(a.desde, ultimo) if a.desde else [a.periodo or ultimo]
        resumen: dict[str, list[str]] = {}
        for periodo in periodos:
            valores = await capturar_mes(db, periodo, guardar_cambios=not a.dry_run)
            resumen[periodo] = [
                f"{v.vertical}.{v.indicador} = {v.valor:,.2f} {v.unidad} ({v.origen})"
                for v in valores
            ] or ["sin datos reales completos"]
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        if a.dry_run:
            await db.rollback()
            print("Dry-run: no se ha guardado nada.")
        else:
            await db.commit()
            print("Guardado.")
    return 0


def main() -> None:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--periodo", help="mes a capturar, AAAA-MM (por defecto, el último cerrado)")
    p.add_argument("--desde", help="captura todos los meses desde AAAA-MM hasta el último cerrado")
    p.add_argument("--estado", action="store_true", help="muestra el origen de cada serie")
    p.add_argument("--dry-run", action="store_true")
    sys.exit(asyncio.run(ejecutar(p.parse_args())))


if __name__ == "__main__":
    main()
