#!/usr/bin/env python3
"""Verificador de la integración de noticias del Ayuntamiento (Strapi).

Comprueba, contra el API público real, que la plataforma puede leer las
noticias municipales: listado general, filtro por la categoría Turismo y
detalle por slug. No modifica nada (solo lectura) ni requiere credenciales.

Uso:

    python -m scripts.verificar_noticias_strapi
    python scripts/verificar_noticias_strapi.py

Lee la misma configuración que la plataforma (``get_settings()``). Devuelve 0
si todo pasa, 1 si hay algún fallo.
"""

from __future__ import annotations

import asyncio
import sys

from nijar_dti.config import get_settings
from nijar_dti.connectors.noticias import ClienteNoticiasStrapi, NoticiasError

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


async def _run() -> int:
    s = get_settings()
    print("\n== Verificación de noticias del Ayuntamiento (Strapi) ==\n")

    if not (s.noticias_strapi_base_url and s.noticias_strapi_project_id):
        _linea(FAIL, "Configuración ausente",
               "faltan NOTICIAS_STRAPI_BASE_URL / NOTICIAS_STRAPI_PROJECT_ID")
        print("\nResultado: FALLA (configuración).\n")
        return 1
    _linea(OK, "Configuración presente",
           f"{s.noticias_strapi_base_url} · project {s.noticias_strapi_project_id}")

    cli = ClienteNoticiasStrapi(
        s.noticias_strapi_base_url, s.noticias_strapi_project_id, s.noticias_timeout_seconds
    )
    fallos = 0

    # 1) Listado general
    try:
        page = await cli.listar(page=1, page_size=3)
        if page["total"] > 0 and page["items"]:
            t0 = page["items"][0]["titulo"][:60]
            _linea(OK, "Listado de noticias accesible",
                   f"{page['total']} noticias · última: «{t0}»")
        else:
            _linea(WARN, "Listado accesible pero vacío", "revisa el project_id")
    except NoticiasError as e:
        _linea(FAIL, "No se puede leer el listado", str(e))
        fallos += 1

    # 2) Categoría Turismo
    if s.noticias_categoria_turismo_id:
        try:
            page = await cli.listar(
                page=1, page_size=1, categoria_document_id=s.noticias_categoria_turismo_id
            )
            if page["total"] > 0:
                _linea(OK, "Filtro por categoría Turismo operativo",
                       f"{page['total']} noticias de Turismo")
            else:
                _linea(WARN, "Categoría Turismo sin noticias",
                       "verifica NOTICIAS_CATEGORIA_TURISMO_ID")
        except NoticiasError as e:
            _linea(FAIL, "Fallo al filtrar por Turismo", str(e))
            fallos += 1
    else:
        _linea(WARN, "NOTICIAS_CATEGORIA_TURISMO_ID sin definir",
               "el atajo /noticias/turismo no filtrará")

    # 3) Detalle por slug + imagen
    try:
        page = await cli.listar(page=1, page_size=1)
        if page["items"]:
            slug = page["items"][0]["slug"]
            det = await cli.por_slug(slug)
            if det and det.get("contenido"):
                img = "con imagen" if det.get("imagen_url") else "sin imagen"
                _linea(OK, "Detalle por slug operativo",
                       f"«{slug[:40]}» · {len(det['contenido'])} car. · {img}")
            else:
                _linea(WARN, "Detalle sin contenido", f"slug {slug}")
    except NoticiasError as e:
        _linea(FAIL, "Fallo al leer el detalle por slug", str(e))
        fallos += 1

    print()
    if fallos:
        print(f"Resultado: FALLA · {fallos} error(es).\n")
        return 1
    print("Resultado: TODO OK. Las noticias del Ayuntamiento se integran correctamente.\n")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
