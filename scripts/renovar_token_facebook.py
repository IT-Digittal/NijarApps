#!/usr/bin/env python3
"""Renovador del token de larga duración de Facebook (Graph API de Meta).

Solo es necesario si se usa un **token de larga duración de ~60 días** (Opción A
del runbook). Si el token es de un **System User** (Opción B, no caduca), este
script NO hace falta.

Qué hace:
  1. Intercambia el token actual por uno nuevo de larga duración
     (``grant_type=fb_exchange_token``), reiniciando la ventana de ~60 días.
  2. Si se apunta a la página (``--page``), re-deriva el **Page Access Token**
     a partir del token de usuario renovado.
  3. Muestra el token nuevo y su caducidad. Con ``--update-env RUTA`` reescribe
     en el sitio la línea ``FACEBOOK_ACCESS_TOKEN=`` de ese ``.env`` (ideal para
     automatizar por cron).

Requiere en el ``.env`` (o por variables de entorno):
  FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_ACCESS_TOKEN (el actual)

Uso:
  python -m scripts.renovar_token_facebook                       # muestra el token nuevo
  python -m scripts.renovar_token_facebook --page                # re-deriva el page token
  python -m scripts.renovar_token_facebook --update-env infra/ovh/.env.production
  python -m scripts.renovar_token_facebook --page --update-env infra/ovh/.env.production --quiet

Códigos de salida: 0 OK · 1 error (no se toca el .env si algo falla).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys

import httpx

from nijar_dti.config import get_settings

GRAPH = "https://graph.facebook.com/v19.0"


def _fmt_exp(expires_in: int | None, expires_at: int | None) -> str:
    ts = None
    if expires_at:
        ts = expires_at
    elif expires_in:
        ts = int(dt.datetime.now(dt.timezone.utc).timestamp()) + expires_in
    if not ts:
        return "sin dato de caducidad"
    f = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    dias = (f - dt.datetime.now(dt.timezone.utc)).days
    return f"caduca {f:%Y-%m-%d} (~{dias} días)"


def _exchange(client: httpx.Client, app_id: str, app_secret: str, token: str) -> tuple[str, str]:
    r = client.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
    )
    if r.status_code >= 400:
        raise RuntimeError(f"intercambio fallido [{r.status_code}]: {_msg(r)}")
    j = r.json()
    nuevo = j.get("access_token")
    if not nuevo:
        raise RuntimeError(f"respuesta sin access_token: {j}")
    return nuevo, _fmt_exp(j.get("expires_in"), j.get("expires_at"))


def _page_token(client: httpx.Client, page_id: str, user_token: str) -> tuple[str, str]:
    r = client.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "access_token,name", "access_token": user_token},
    )
    if r.status_code >= 400:
        raise RuntimeError(f"no se pudo obtener el page token [{r.status_code}]: {_msg(r)}")
    j = r.json()
    tok = j.get("access_token")
    if not tok:
        raise RuntimeError("la respuesta de la página no incluye access_token "
                           "(¿el token de usuario tiene pages_read_engagement?)")
    # Verifica caducidad del page token derivado (los derivados de long-lived no caducan)
    exp = "no caduca (derivado de token de larga duración)"
    d = client.get(f"{GRAPH}/debug_token",
                   params={"input_token": tok, "access_token": user_token})
    if d.status_code < 400:
        data = d.json().get("data", {})
        if data.get("expires_at"):
            exp = _fmt_exp(None, data["expires_at"])
        elif data.get("expires_at") == 0:
            exp = "no caduca"
    return tok, exp


def _update_env(path: str, nuevo: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        lineas = f.readlines()
    patron = re.compile(r"^\s*FACEBOOK_ACCESS_TOKEN\s*=")
    encontrado = False
    for i, ln in enumerate(lineas):
        if patron.match(ln):
            lineas[i] = f"FACEBOOK_ACCESS_TOKEN={nuevo}\n"
            encontrado = True
            break
    if not encontrado:
        lineas.append(f"FACEBOOK_ACCESS_TOKEN={nuevo}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lineas)


def _msg(r: httpx.Response) -> str:
    try:
        return r.json().get("error", {}).get("message", r.text[:160])
    except ValueError:
        return r.text[:160]


def main() -> int:
    ap = argparse.ArgumentParser(description="Renueva el token de larga duración de Facebook.")
    ap.add_argument("--page", action="store_true",
                    help="re-derivar el Page Access Token (usa FACEBOOK_PAGE_ID)")
    ap.add_argument("--update-env", metavar="RUTA",
                    help="reescribe FACEBOOK_ACCESS_TOKEN en ese archivo .env")
    ap.add_argument("--quiet", action="store_true", help="no imprime el token en claro")
    args = ap.parse_args()

    s = get_settings()
    if not (s.facebook_app_id and s.facebook_app_secret and s.facebook_access_token):
        print("FALTA configuración: se requieren FACEBOOK_APP_ID, FACEBOOK_APP_SECRET "
              "y FACEBOOK_ACCESS_TOKEN.", file=sys.stderr)
        return 1

    try:
        with httpx.Client(timeout=25) as client:
            nuevo, exp = _exchange(client, s.facebook_app_id, s.facebook_app_secret,
                                   s.facebook_access_token)
            destino = "token de usuario (larga duración)"
            if args.page:
                if not s.facebook_page_id:
                    print("Se pidió --page pero falta FACEBOOK_PAGE_ID.", file=sys.stderr)
                    return 1
                nuevo, exp = _page_token(client, s.facebook_page_id, nuevo)
                destino = "Page Access Token"
    except (RuntimeError, httpx.HTTPError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"✔ Token renovado ({destino}) · {exp}")
    if not args.quiet:
        print(f"  FACEBOOK_ACCESS_TOKEN={nuevo}")

    if args.update_env:
        try:
            _update_env(args.update_env, nuevo)
            print(f"✔ Archivo actualizado: {args.update_env} "
                  "(reinicia el social-worker para aplicarlo)")
        except OSError as e:
            print(f"ERROR al escribir {args.update_env}: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
