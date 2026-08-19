#!/usr/bin/env python3
"""Verificador de credenciales de Google Analytics 4 (Reporting Data API).

Comprueba, contra la API real de GA4, que la **cuenta de servicio** y el
**Property ID** configurados funcionan ANTES de dar por integrada la analítica
web. No modifica nada: solo hace una consulta de lectura mínima.

Uso:

    python -m scripts.verificar_ga4        # desde la raíz del repo
    python scripts/verificar_ga4.py

Lee la misma configuración que la plataforma (``get_settings()``), así que valida
exactamente lo que usará el dashboard y el informe mensual. Devuelve 0 si todo
pasa, 1 si hay algún fallo.
"""

from __future__ import annotations

import json
import os
import sys

import httpx

from nijar_dti.config import get_settings

GA4_API = "https://analyticsdata.googleapis.com/v1beta"
SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


def _cargar_sa(valor: str) -> dict:
    """Devuelve el dict del service account desde ruta o JSON inline."""
    if os.path.exists(valor):
        with open(valor, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(valor)


def main() -> int:
    s = get_settings()
    print("\n== Verificación de Google Analytics 4 (Reporting Data API) ==\n")

    prop = getattr(s, "ga4_property_id", "")
    sa_raw = getattr(s, "ga4_service_account_json", "")

    if not prop:
        _linea(FAIL, "GA4_PROPERTY_ID ausente", "es el ID numérico de la propiedad GA4")
    else:
        _linea(OK, "GA4_PROPERTY_ID presente", prop)
    if not sa_raw:
        _linea(FAIL, "GA4_SERVICE_ACCOUNT_JSON ausente", "ruta al JSON o JSON inline")
    if not prop or not sa_raw:
        print("\nResultado: FALLA (falta configuración).\n")
        return 1

    # 1) google-auth instalado (y su backend de criptografía operativo)
    try:
        from google.auth.transport.requests import Request  # type: ignore
        from google.oauth2 import service_account  # type: ignore
        _linea(OK, "Dependencia google-auth disponible")
    except ImportError:
        _linea(FAIL, "Falta la dependencia google-auth",
               "instala 'google-auth>=2.27' (ya añadida a pyproject)")
        print("\nResultado: FALLA (dependencia ausente).\n")
        return 1
    except BaseException as e:  # noqa: BLE001 — backend nativo de 'cryptography' roto (pyo3 panic)
        _linea(FAIL, "google-auth instalado pero no operativo",
               f"{type(e).__name__}: {str(e)[:120]} (revisa 'cryptography'/'cffi')")
        print("\nResultado: FALLA (dependencia rota).\n")
        return 1

    # 2) Cargar y validar el service account
    try:
        info = _cargar_sa(sa_raw)
        email = info.get("client_email", "?")
        origen = "fichero" if os.path.exists(sa_raw) else "JSON inline"
        _linea(OK, "Cuenta de servicio cargada", f"{email} (desde {origen})")
    except (OSError, json.JSONDecodeError) as e:
        _linea(FAIL, "No se pudo leer GA4_SERVICE_ACCOUNT_JSON", str(e))
        print("\nResultado: FALLA (service account ilegible).\n")
        return 1

    # 3) Obtener token OAuth2
    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])
        creds.refresh(Request())
        _linea(OK, "Token OAuth2 obtenido", "autenticación de la cuenta de servicio correcta")
    except Exception as e:  # noqa: BLE001 — google-auth lanza varios tipos
        _linea(FAIL, "No se pudo autenticar la cuenta de servicio", str(e)[:160])
        print("\nResultado: FALLA (autenticación).\n")
        return 1

    # 4) Consulta mínima runReport contra la propiedad
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(
                f"{GA4_API}/properties/{prop}:runReport",
                headers={"Authorization": f"Bearer {creds.token}"},
                json={
                    "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                    "metrics": [{"name": "sessions"}, {"name": "totalUsers"}],
                },
            )
        if r.status_code < 400:
            rows = r.json().get("rows") or []
            if rows:
                vals = [m.get("value") for m in rows[0].get("metricValues", [])]
                _linea(OK, "GA4 responde con datos",
                       f"últimos 7 días → sesiones={vals[0]}, usuarios={vals[1]}")
            else:
                _linea(WARN, "GA4 responde correctamente pero sin filas",
                       "la propiedad puede no tener tráfico en el rango")
        elif r.status_code == 403:
            _linea(FAIL, "GA4 deniega el acceso (403)",
                   f"da permiso de VISUALIZADOR a {email} en la propiedad {prop}")
            print("\nResultado: FALLA (permisos en GA4).\n")
            return 1
        else:
            _linea(FAIL, f"GA4 devuelve error {r.status_code}", _err(r))
            print("\nResultado: FALLA (API).\n")
            return 1
    except httpx.HTTPError as e:
        _linea(FAIL, "Error de red al consultar GA4", str(e))
        print("\nResultado: FALLA (red).\n")
        return 1

    print("\nResultado: TODO OK. La analítica GA4 real está operativa "
          "(dashboard e informe mensual).\n")
    return 0


def _err(r: httpx.Response) -> str:
    try:
        e = r.json().get("error", {})
        return f"[{r.status_code}] {e.get('message', r.text[:140])}"
    except ValueError:
        return f"[{r.status_code}] {r.text[:140]}"


if __name__ == "__main__":
    sys.exit(main())
