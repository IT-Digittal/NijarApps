#!/usr/bin/env python3
"""Verificación global de todas las integraciones externas de la plataforma.

Ejecuta cada verificador individual y muestra un resumen compacto (OK / FALLA)
por integración. Útil como comprobación previa a un despliegue o para diagnóstico.

Uso:
    python -m scripts.verificar_integraciones            # resumen compacto
    python -m scripts.verificar_integraciones --detalle  # + informe de cada uno

Código de salida: 0 si todas pasan, 1 si alguna falla. Las integraciones que
dependen de credenciales aún no facilitadas se reportan como FALLA de
configuración (esperado hasta que se activen).
"""

from __future__ import annotations

import contextlib
import importlib
import io
import sys

VERIFICADORES = [
    ("Noticias (Strapi)", "scripts.verificar_noticias_strapi"),
    ("Meteo pública (Open-Meteo)", "scripts.verificar_openmeteo"),
    ("Banderas/Aforo (ThingsBoard)", "scripts.verificar_thingsboard"),
    ("Social Listening (Meta)", "scripts.verificar_social_meta"),
    ("Google Analytics 4", "scripts.verificar_ga4"),
]


def _resumen(salida: str) -> str:
    for linea in reversed(salida.splitlines()):
        if linea.strip().startswith("Resultado:"):
            return linea.strip()
    return "(sin resumen)"


def main() -> int:
    detalle = "--detalle" in sys.argv or "-v" in sys.argv
    print("\n== Verificación global de integraciones · Plataforma DTI Níjar ==\n")

    filas: list[tuple[str, int, str, str]] = []
    for nombre, modulo in VERIFICADORES:
        buf = io.StringIO()
        try:
            mod = importlib.import_module(modulo)
            with contextlib.redirect_stdout(buf):
                code = mod.main()
        except BaseException as exc:  # noqa: BLE001 — runner diagnóstico; nunca abortar
            code = 1
            buf.write(f"Resultado: FALLA ({type(exc).__name__}: {str(exc)[:80]})")
        filas.append((nombre, int(code), _resumen(buf.getvalue()), buf.getvalue()))

    if detalle:
        for nombre, _code, _res, salida in filas:
            print(f"----- {nombre} -----")
            print(salida.strip() or "(sin salida)")
            print()

    ancho = max(len(n) for n, _, _, _ in filas)
    fallos = 0
    for nombre, code, res, _salida in filas:
        icono = "\033[92m  OK \033[0m" if code == 0 else "\033[91mFALLA\033[0m"
        print(f"  [{icono}]  {nombre.ljust(ancho)}   {res}")
        if code != 0:
            fallos += 1

    print()
    print(f"{len(filas) - fallos}/{len(filas)} integraciones en verde.")
    if fallos:
        print("Nota: las integraciones pendientes de credenciales fallan por "
              "configuración hasta que se activen (ver docs/integraciones/README.md).")
    print()
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
