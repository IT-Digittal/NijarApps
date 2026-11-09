"""CLI: importa una carpeta de ordenanzas en PDF (descargadas de la sede electrónica).

Uso (en producción, con la carpeta copiada al contenedor):

    # Comprobar qué se importaría (lee los PDF y su texto, no guarda nada)
    python -m nijar_dti.workers.importar_normativa /tmp/ordenanzas --dry-run

    # Importar (o actualizar: un PDF ya importado no se duplica)
    python -m nijar_dti.workers.importar_normativa /tmp/ordenanzas

Si la carpeta tiene un ``manifest.csv``, se usan sus títulos, URL y fechas.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from nijar_dti.services import normativa_service as svc


async def importar(carpeta: Path, dry_run: bool) -> dict[str, Any]:
    from nijar_dti.core.database import AsyncSessionLocal

    manifest = carpeta / "manifest.csv"
    indice = svc.leer_manifest(manifest.read_bytes()) if manifest.is_file() else {}
    resumen: dict[str, Any] = {
        "pdf": 0,
        "importadas": 0,
        "actualizadas": 0,
        "sin_texto": [],
        "errores": [],
        "manifest": manifest.is_file(),
        "por_tipo": {},
    }
    async with AsyncSessionLocal() as db:
        for ruta in sorted(carpeta.glob("*.pdf")) + sorted(carpeta.glob("*.PDF")):
            resumen["pdf"] += 1
            datos = svc.datos_de_manifest(indice.get(ruta.name))
            try:
                async with db.begin_nested():
                    norma, nueva = await svc.importar_pdf(
                        db,
                        ruta.read_bytes(),
                        ruta.name,
                        titulo=datos["titulo"],
                        url_origen=datos["url"],
                        fecha_publicacion=datos["fecha"],
                        guardar_fichero=not dry_run,
                    )
            except Exception as exc:  # noqa: BLE001
                resumen["errores"].append(f"{ruta.name}: {exc}")
                continue
            resumen["importadas" if nueva else "actualizadas"] += 1
            resumen["por_tipo"][norma.tipo] = resumen["por_tipo"].get(norma.tipo, 0) + 1
            if not norma.texto:
                resumen["sin_texto"].append(ruta.name)
        if dry_run:
            await db.rollback()
        else:
            await db.commit()
    return resumen


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Importa ordenanzas en PDF a la plataforma")
    p.add_argument("carpeta", type=Path)
    p.add_argument("--dry-run", action="store_true", help="Solo comprobar, sin guardar")
    a = p.parse_args(argv)
    if not a.carpeta.is_dir():
        p.error(f"No existe la carpeta {a.carpeta}")
    resumen = asyncio.run(importar(a.carpeta, a.dry_run))
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    if a.dry_run:
        print("Dry-run: no se ha guardado nada.")
    return 1 if resumen["errores"] else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
