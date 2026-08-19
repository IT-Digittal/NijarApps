"""Utilidades de exportación (CSV) para informes y explotación externa.

Cumple el requisito del pliego de exportar los datos/KPIs en formatos
abiertos (CSV/JSON) para su explotación y auditoría.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def csv_response(filas: Iterable[BaseModel | dict], nombre: str) -> StreamingResponse:
    """Devuelve una respuesta ``text/csv`` a partir de modelos Pydantic o dicts."""
    filas = list(filas)
    registros: list[dict] = [f.model_dump() if isinstance(f, BaseModel) else dict(f) for f in filas]
    buf = io.StringIO()
    campos = list(registros[0].keys()) if registros else []
    writer = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    for r in registros:
        writer.writerow(
            {
                k: (";".join(map(str, v)) if isinstance(v, (list, tuple)) else v)
                for k, v in r.items()
            }
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}.csv"'},
    )
