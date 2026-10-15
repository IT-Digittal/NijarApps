#!/usr/bin/env python3
"""Verificador de la integración Datadis (consumo eléctrico) · vertical de Energía.

1. **Datos públicos** (``/api-public/api-search``): prueba la consulta de una
   semana reciente SIN credenciales (y con ellas si Datadis las exige), con
   varios formatos del código de municipio, y dice cuál devuelve filas de
   Níjar. Muestra también una fila de ejemplo tal como la envía Datadis.
2. **API privada**: si hay ``DATADIS_USUARIO``/``DATADIS_PASSWORD``, inicia
   sesión y lista los suministros (CUPS) accesibles.

Solo lectura. Uso (en producción):
    docker exec -i nijar-dti-api python - < scripts/verificar_datadis.py
    python -m scripts.verificar_datadis
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, timedelta

from nijar_dti.config import get_settings
from nijar_dti.connectors.datadis import (
    DatadisAutenticacionError,
    DatadisError,
    normalizar,
    parsear_registro_publico,
)
from nijar_dti.services import datadis_service as svc

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


def _variantes(codigo: str) -> list[str]:
    """Formatos plausibles del filtro de municipio (provincia+municipio INE)."""
    c = codigo.strip()
    prov, mun = c[:2], c[2:]
    vistas = []
    for v in (c, f"{prov}-{mun}", f"{prov};{mun}", str(int(c)) if c.isdigit() else c, mun):
        if v and v not in vistas:
            vistas.append(v)
    return vistas


async def _publico() -> tuple[bool, str | None]:
    s = get_settings()
    hasta = date.today() - timedelta(days=3)
    desde = hasta - timedelta(days=6)
    if desde.month != hasta.month:  # Datadis: el rango debe caer en un mismo mes
        desde = hasta.replace(day=1)
    print(f"  Consulta pública de prueba: {desde:%d/%m/%Y} – {hasta:%d/%m/%Y}\n")
    nombre = normalizar(s.datadis_municipio_nombre)
    mejor: str | None = None
    mezclado: str | None = None  # devuelve Níjar pero sin aplicar el filtro de municipio
    ejemplo_mostrado = False
    async with svc.nuevo_cliente(s) as cli:
        for codigo in _variantes(s.datadis_municipio_codigo):
            try:
                filas, primera = await cli.buscar_publico(
                    desde, hasta, svc.filtros_publicos(s, codigo), page_size=200, max_paginas=1
                )
            except DatadisAutenticacionError as e:
                _linea(FAIL, "Datadis exige usuario también para los datos públicos", str(e))
                if not svc.datadis_configurado(s):
                    print(
                        "     → Hay que dar de alta un usuario en datadis.es y configurar "
                        "DATADIS_USUARIO / DATADIS_PASSWORD."
                    )
                return False, None
            except DatadisError as e:
                _linea(WARN, f"provinceMunicipality={codigo!r}", f"error: {e}")
                continue
            regs = [r for r in (parsear_registro_publico(f) for f in filas) if r]
            municipios = sorted({normalizar(r.municipio) for r in regs if r.municipio})
            de_nijar = [r for r in regs if not r.municipio or nombre in normalizar(r.municipio)]
            detalle = (f"{len(filas)} filas · {len(regs)} interpretables · "
                       f"municipios: {', '.join(municipios[:4]) or '—'}"
                       + (" …" if len(municipios) > 4 else ""))  # fmt: skip
            correcto = bool(de_nijar) and municipios in ([], [nombre])
            _linea(OK if correcto else WARN, f"provinceMunicipality={codigo!r}", detalle)
            if filas and not ejemplo_mostrado:
                ejemplo_mostrado = True
                print("     Ejemplo de fila tal como la envía Datadis:")
                print("     " + json.dumps(filas[0], ensure_ascii=False)[:400])
                if not regs:
                    print(
                        f"     {WARN} El formato no se reconoce: envía esta línea al equipo"
                        " técnico para ajustar el conector."
                    )
                    if isinstance(primera, dict):
                        print("     Claves de la respuesta: " + ", ".join(list(primera)[:12]))
            if correcto and mejor is None:
                mejor = codigo
            elif de_nijar and mezclado is None:
                mezclado = codigo
    print()
    if mejor is None and mezclado is not None:
        _linea(
            WARN,
            "Hay datos de Níjar, pero Datadis no aplica el filtro de municipio",
            "la carga los separa por nombre; con toda la comunidad puede faltar algún día",
        )
        return True, mezclado
    if mejor is None:
        _linea(
            FAIL,
            "Ninguna consulta devolvió filas de Níjar",
            "revisar DATADIS_MUNICIPIO_CODIGO o el rango de fechas",
        )
        return False, None
    total = "configurado" if mejor == s.datadis_municipio_codigo else "recomendado"
    _linea(OK, "Datos públicos de Níjar accesibles",
           f"DATADIS_MUNICIPIO_CODIGO={mejor} ({total})")  # fmt: skip
    return True, mejor


async def _privado() -> bool | None:
    if not svc.datadis_configurado():
        _linea(
            WARN,
            "API privada sin configurar",
            "faltan DATADIS_USUARIO / DATADIS_PASSWORD (pendiente del Ayuntamiento)",
        )
        return None
    try:
        async with svc.nuevo_cliente() as cli:
            await cli.login()
            _linea(OK, "Login en Datadis correcto")
            sums = await cli.suministros()
    except DatadisError as e:
        _linea(FAIL, "API privada no accesible", str(e))
        return False
    if not sums:
        _linea(WARN, "Login correcto pero sin suministros",
               "¿falta la autorización o DATADIS_NIF_AUTORIZADO?")  # fmt: skip
        return False
    distribuidoras = sorted({s.distribuidora or "?" for s in sums})
    _linea(OK, f"{len(sums)} suministros (CUPS) accesibles", ", ".join(distribuidoras))
    for s in sums[:3]:
        print(f"     · {s.cups[:8]}…  {s.direccion[:60]}")
    return True


async def _run() -> int:
    print("\n== Verificación de la integración Datadis (consumo eléctrico) ==\n")
    publico_ok, _ = await _publico()
    print()
    privado = await _privado()
    print()
    if not publico_ok or privado is False:
        print("Resultado: FALLA" + (" (datos públicos)" if not publico_ok else " (API privada)")
              + ".\n")  # fmt: skip
        return 1
    extra = "" if privado else " API privada pendiente de credenciales."
    print(f"Resultado: OK. Datos públicos de Níjar disponibles.{extra}\n")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
