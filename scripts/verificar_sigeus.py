#!/usr/bin/env python3
"""Verificador de la integración siGEUS (Plataforma Distromel): RSU y limpieza viaria.

Comprueba que la plataforma puede iniciar sesión en el backend de siGEUS con
el usuario técnico facilitado, leer el perfil y validar la sesión. Requiere
``SIGEUS_USUARIO`` y ``SIGEUS_PASSWORD``. Solo lectura.

Uso:
    python -m scripts.verificar_sigeus
    python scripts/verificar_sigeus.py
"""

from __future__ import annotations

import asyncio
import sys

from nijar_dti.connectors.sigeus import SigeusError, SigeusRequiere2FAError
from nijar_dti.services import sigeus_service as svc

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


async def _run() -> int:
    print("\n== Verificación de la integración siGEUS (Distromel · RSU y limpieza viaria) ==\n")
    if not svc.sigeus_configurado():
        _linea(FAIL, "siGEUS sin configurar", "faltan SIGEUS_USUARIO / SIGEUS_PASSWORD")
        print("\nResultado: FALLA (configuración).\n")
        return 1
    _linea(OK, "Configuración presente")

    try:
        acceso = await svc.comprobar_acceso()
    except SigeusRequiere2FAError as e:
        _linea(FAIL, f"La cuenta exige segundo factor ({e.modo or 'modo desconocido'})", str(e))
        if e.modo == "TOTP":
            print(
                "\nResultado: FALLA · configurar SIGEUS_TOTP_SECRET con el secreto "
                "del autenticador.\n"
            )
        else:
            print(
                "\nResultado: FALLA · cambiar la cuenta a autenticador (TOTP) y configurar "
                "SIGEUS_TOTP_SECRET, o pedir a Distromel un usuario técnico sin 2FA.\n"
            )
        return 1
    except SigeusError as e:
        _linea(FAIL, "No se puede iniciar sesión en siGEUS", str(e))
        print("\nResultado: FALLA · 1 error(es).\n")
        return 1

    usuario = acceso["usuario"]
    nombre = usuario.get("userName") or usuario.get("username") or usuario.get("name") or "?"
    _linea(OK, "Login correcto", f"usuario «{nombre}»")
    cc, sc = acceso["customer_code"], acceso["site_code"]
    if cc is not None or sc is not None:
        _linea(OK, "Explotación asignada", f"customerCode={cc} · siteCode={sc}")
    else:
        _linea(WARN, "El token no indica explotación", "fijar SIGEUS_CUSTOMER_CODE / SITE_CODE")
    if acceso["sesion_valida"]:
        _linea(OK, "Sesión validada por el backend (checkAuthAsync)")
    else:
        _linea(WARN, "checkAuthAsync no confirma la sesión", "revisar códigos de explotación")

    print()
    print(
        "Resultado: TODO OK. Acceso a siGEUS operativo; siguiente paso: capturar los "
        "endpoints de RSU/limpieza del panel y volcarlos a la vertical Residuos.\n"
    )
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
