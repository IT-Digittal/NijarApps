"""Worker/CLI de backfill de contexto histórico.

Ejecuta los conectores de fuentes públicas (INE Frontur/Egatur/EOH, Junta de
Andalucía, AENA) y genera un dataset normalizado al modelo semántico, listo
para enviarse a ``POST /api/v1/data/contexto/ingest``.

Uso:

    # Genera el dataset sintético (sin red) y lo escribe a un fichero JSON
    python -m nijar_dti.workers.contexto_backfill --dry-run --output dataset_contexto.json

    # Imprime un resumen por consola
    python -m nijar_dti.workers.contexto_backfill --dry-run

El factor de expansión preliminar se calcula a partir de las pernoctaciones
EOH del último periodo disponible en el propio dataset.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from nijar_dti.connectors.contexto.expansion import calcular_factor_expansion
from nijar_dti.connectors.contexto.fuentes import todos_los_conectores


def generar_dataset(dry_run: bool = True, anios: int = 3) -> dict:
    """Construye el dataset {registros: [...]} ejecutando todos los conectores."""
    registros = []
    for conector in todos_los_conectores(dry_run=dry_run):
        for rec in conector.fetch_series(anios=anios):
            registros.append(asdict(rec))
    return {"registros": registros}


def _ultimo_eoh(registros: list[dict]) -> float | None:
    eoh = [r for r in registros if r["fuente"] == "ine_eoh" and r["indicador"] == "pernoctaciones"]
    if not eoh:
        return None
    eoh.sort(key=lambda r: r["periodo"])
    return float(eoh[-1]["valor"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill de contexto histórico DTI Níjar")
    parser.add_argument("--dry-run", action="store_true", help="Usa series sintéticas (sin red)")
    parser.add_argument("--anios", type=int, default=3, help="Años de histórico a generar")
    parser.add_argument("--output", type=str, default=None, help="Ruta del JSON de salida")
    args = parser.parse_args(argv)

    dataset = generar_dataset(dry_run=args.dry_run, anios=args.anios)
    registros = dataset["registros"]

    pernoctaciones = _ultimo_eoh(registros)
    fe = calcular_factor_expansion(pernoctaciones_periodo=pernoctaciones)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(dataset, fh, ensure_ascii=False, indent=2)
        print(f"Dataset escrito en {args.output} ({len(registros)} registros)")
    else:
        print(json.dumps(dataset, ensure_ascii=False, indent=2))

    # Resumen por fuente
    por_fuente: dict[str, int] = {}
    for r in registros:
        por_fuente[r["fuente"]] = por_fuente.get(r["fuente"], 0) + 1
    print("\nResumen backfill contexto:", file=sys.stderr)
    for fuente, n in sorted(por_fuente.items()):
        print(f"  - {fuente}: {n} registros", file=sys.stderr)
    print(
        f"Factor de expansión preliminar: {fe.factor} "
        f"(cobertura ~{fe.cobertura_estimada_pct}%, método={fe.metodo})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
