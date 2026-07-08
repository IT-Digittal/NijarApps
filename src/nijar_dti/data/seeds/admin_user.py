"""Usuario administrador inicial.

La contraseña por defecto debe cambiarse inmediatamente tras el primer
arranque (clave en `.env` o variable de entorno `INITIAL_ADMIN_PASSWORD`).
"""

from __future__ import annotations

import os

from nijar_dti.core.security import hash_password


_DEFAULT_ADMIN_PASSWORD = "CambiarEnPrimerArranque#2026"
_DEFAULT_DIRECCION_PASSWORD = "Direccion#Nijar2026"


def _resolve_password() -> str:
    return os.environ.get("INITIAL_ADMIN_PASSWORD", _DEFAULT_ADMIN_PASSWORD)


def _resolve_direccion_password() -> str:
    return os.environ.get("INITIAL_DIRECCION_PASSWORD", _DEFAULT_DIRECCION_PASSWORD)


ADMIN_USER_SEED: dict[str, object] = {
    "email": os.environ.get("INITIAL_ADMIN_EMAIL", "admin@nijar.es"),
    "nombre_completo": "Administrador TIC",
    "rol": "administrador_tic",
    "scopes_adicionales": [],
    "activo": True,
    "requiere_2fa": True,
    "_password": _resolve_password,  # función para no evaluar en import
}

# Usuario demostrativo con el perfil directivo/político "Dirección / Gobierno".
DIRECCION_USER_SEED: dict[str, object] = {
    "email": os.environ.get("INITIAL_DIRECCION_EMAIL", "direccion@nijar.es"),
    "nombre_completo": "Dirección / Gobierno",
    "rol": "direccion_gobierno",
    "scopes_adicionales": [],
    "activo": True,
    "requiere_2fa": True,
    "_password": _resolve_direccion_password,
}


def admin_password_hash() -> str:
    """Hash bcrypt de la contraseña inicial (calculado en el momento del seed)."""
    return hash_password(_resolve_password())


def direccion_password_hash() -> str:
    """Hash bcrypt de la contraseña inicial del usuario de dirección."""
    return hash_password(_resolve_direccion_password())
