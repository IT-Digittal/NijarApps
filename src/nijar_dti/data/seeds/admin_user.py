"""Usuario administrador inicial.

La contraseña por defecto debe cambiarse inmediatamente tras el primer
arranque (clave en `.env` o variable de entorno `INITIAL_ADMIN_PASSWORD`).
"""

from __future__ import annotations

import os

from nijar_dti.core.security import hash_password


_DEFAULT_ADMIN_PASSWORD = "CambiarEnPrimerArranque#2026"


def _resolve_password() -> str:
    return os.environ.get("INITIAL_ADMIN_PASSWORD", _DEFAULT_ADMIN_PASSWORD)


ADMIN_USER_SEED: dict = {
    "email": os.environ.get("INITIAL_ADMIN_EMAIL", "admin@nijar.es"),
    "nombre_completo": "Administrador TIC",
    "rol": "administrador_tic",
    "scopes_adicionales": [],
    "activo": True,
    "requiere_2fa": True,
    "_password": _resolve_password,  # función para no evaluar en import
}


def admin_password_hash() -> str:
    """Hash bcrypt de la contraseña inicial (calculado en el momento del seed)."""
    return hash_password(_resolve_password())
