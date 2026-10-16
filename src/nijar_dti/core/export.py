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


def csv_response(
    filas: Iterable[BaseModel | dict],
    nombre: str,
    *,
    separador: str = ",",
    excel: bool = False,
) -> StreamingResponse:
    """Devuelve una respuesta ``text/csv`` a partir de modelos Pydantic o dicts.

    Con ``excel=True`` usa «;» y BOM UTF-8, que es lo que Excel en español abre
    directamente en columnas y con las tildes correctas.
    """
    if excel:
        separador = ";"
    filas = list(filas)
    registros: list[dict] = [f.model_dump() if isinstance(f, BaseModel) else dict(f) for f in filas]
    buf = io.StringIO()
    campos = list(registros[0].keys()) if registros else []
    if excel:
        buf.write("\ufeff")
    writer = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore", delimiter=separador)
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
