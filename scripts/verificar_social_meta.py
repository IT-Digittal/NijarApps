#!/usr/bin/env python3
"""Verificador de credenciales de Social Listening (Meta: Facebook + Instagram).

Comprueba, contra la Graph API real, que el token y los IDs configurados en el
``.env`` funcionan ANTES de poner ``SOCIAL_DRY_RUN=false`` y activar el worker.

Uso:

    python -m scripts.verificar_social_meta        # desde la raíz del repo
    python scripts/verificar_social_meta.py

No modifica nada: solo hace peticiones de lectura y muestra un informe con el
estado de cada comprobación. Devuelve código de salida 0 si todo pasa, 1 si hay
algún fallo (útil para CI o para un check previo al despliegue).

Lee la misma configuración que el worker (``get_settings()``), así que valida
exactamente lo que usará la plataforma en producción.
"""

from __future__ import annotations

import sys

import httpx

from nijar_dti.config import get_settings

# Misma versión de la Graph API que usan los conectores del repo.
GRAPH = "https://graph.facebook.com/v19.0"

OK = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
WARN = "\033[93m▲\033[0m"


def _linea(estado: str, titulo: str, detalle: str = "") -> None:
    print(f"  {estado}  {titulo}" + (f"  —  {detalle}" if detalle else ""))


def main() -> int:
    s = get_settings()
    fallos = 0
    avisos = 0

    print("\n== Verificación de Social Listening · Meta (Facebook + Instagram) ==\n")

    # 0) DRY_RUN informativo
    if s.social_dry_run:
        _linea(WARN, "SOCIAL_DRY_RUN=true", "ahora mismo se usan datos sintéticos; "
               "cámbialo a false cuando esta verificación pase en verde")
        avisos += 1
    else:
        _linea(OK, "SOCIAL_DRY_RUN=false", "modo real activado")

    token = s.facebook_access_token
    page_ref = s.facebook_page_id or s.facebook_page_handle
    ig_id = s.instagram_business_account_id

    if not token:
        _linea(FAIL, "FACEBOOK_ACCESS_TOKEN ausente", "no se puede verificar nada más")
        print("\nResultado: FALLA (falta el token).\n")
        return 1

    with httpx.Client(timeout=20) as client:
        # 1) Identidad y validez del token
        try:
            r = client.get(f"{GRAPH}/me", params={"fields": "id,name", "access_token": token})
            if r.status_code < 400:
                me = r.json()
                _linea(OK, "Token válido", f"identidad: {me.get('name')} (id {me.get('id')})")
            else:
                _linea(FAIL, "Token rechazado por la Graph API", _err(r))
                fallos += 1
        except httpx.HTTPError as e:
            _linea(FAIL, "Error de red al validar el token", str(e))
            fallos += 1

        # 1b) Caducidad del token (debug_token; puede requerir app token, se tolera)
        try:
            r = client.get(f"{GRAPH}/debug_token",
                           params={"input_token": token, "access_token": token})
            if r.status_code < 400:
                d = r.json().get("data", {})
                exp = d.get("expires_at")
                scopes = d.get("scopes", [])
                if exp == 0:
                    _linea(OK, "El token NO caduca", "recomendado (System User)")
                elif exp:
                    import datetime as _dt
                    f = _dt.datetime.fromtimestamp(exp, _dt.timezone.utc)
                    dias = (f - _dt.datetime.now(_dt.timezone.utc)).days
                    est = OK if dias > 14 else WARN
                    if dias <= 14:
                        avisos += 1
                    _linea(est, "Caducidad del token", f"expira {f:%Y-%m-%d} ({dias} días)")
                _verificar_scopes(scopes)
            else:
                _linea(WARN, "No se pudo inspeccionar la caducidad/scopes del token",
                       "(normal si no se usa app token) " + _err(r))
                avisos += 1
        except httpx.HTTPError:
            _linea(WARN, "No se pudo inspeccionar la caducidad del token", "")
            avisos += 1

        # 2) Facebook: lectura del feed de la página
        if not page_ref:
            _linea(FAIL, "FACEBOOK_PAGE_ID / HANDLE ausente", "sin esto no se lee el feed")
            fallos += 1
        else:
            try:
                r = client.get(f"{GRAPH}/{page_ref}/feed",
                               params={"fields": "id,created_time", "limit": 1, "access_token": token})
                if r.status_code < 400:
                    n = len(r.json().get("data", []))
                    _linea(OK, "Facebook · feed de la página accesible",
                           f"{n} post(s) leído(s) en la prueba (ref: {page_ref})")
                else:
                    _linea(FAIL, "Facebook · no se puede leer el feed", _err(r))
                    fallos += 1
            except httpx.HTTPError as e:
                _linea(FAIL, "Facebook · error de red", str(e))
                fallos += 1

        # 3) Instagram: cuenta business + búsqueda de hashtag
        if not ig_id:
            _linea(FAIL, "INSTAGRAM_BUSINESS_ACCOUNT_ID ausente", "sin esto no hay IG")
            fallos += 1
        else:
            try:
                r = client.get(f"{GRAPH}/{ig_id}",
                               params={"fields": "username,name", "access_token": token})
                if r.status_code < 400:
                    j = r.json()
                    _linea(OK, "Instagram · cuenta business accesible",
                           f"@{j.get('username', '?')}")
                else:
                    _linea(FAIL, "Instagram · no se puede leer la cuenta", _err(r))
                    fallos += 1
            except httpx.HTTPError as e:
                _linea(FAIL, "Instagram · error de red", str(e))
                fallos += 1

            # 3b) hashtag search (un solo hashtag de prueba)
            tags = [h.strip().lstrip("#") for h in s.instagram_hashtags.split(",") if h.strip()]
            tag = tags[0] if tags else "nijar"
            try:
                r = client.get(f"{GRAPH}/ig_hashtag_search",
                               params={"user_id": ig_id, "q": tag, "access_token": token})
                if r.status_code < 400 and r.json().get("data"):
                    _linea(OK, "Instagram · búsqueda de hashtags operativa",
                           f"#{tag} resuelto correctamente")
                elif r.status_code < 400:
                    _linea(WARN, "Instagram · hashtag search respondió vacío",
                           f"#{tag} sin resultados (revisa el hashtag)")
                    avisos += 1
                else:
                    _linea(FAIL, "Instagram · hashtag search falla",
                           _err(r) + "  (¿falta instagram_manage_insights?)")
                    fallos += 1
            except httpx.HTTPError as e:
                _linea(FAIL, "Instagram · error de red en hashtag search", str(e))
                fallos += 1

    print()
    if fallos:
        print(f"Resultado: FALLA · {fallos} error(es), {avisos} aviso(s). "
              "Mantén SOCIAL_DRY_RUN=true y revisa el runbook.\n")
        return 1
    if avisos:
        print(f"Resultado: OK con {avisos} aviso(s). Puedes activar SOCIAL_DRY_RUN=false.\n")
        return 0
    print("Resultado: TODO OK. Puedes poner SOCIAL_DRY_RUN=false y reiniciar el social-worker.\n")
    return 0


def _verificar_scopes(scopes: list[str]) -> None:
    requeridos = {
        "pages_read_engagement": "leer el feed de Facebook",
        "instagram_basic": "acceso básico a Instagram",
        "instagram_manage_insights": "búsqueda de hashtags de Instagram",
    }
    faltan = [f"{sc} ({desc})" for sc, desc in requeridos.items() if sc not in scopes]
    if not scopes:
        return
    if faltan:
        _linea(WARN, "Faltan permisos en el token", "; ".join(faltan))
    else:
        _linea(OK, "Permisos (scopes) correctos", ", ".join(requeridos))


def _err(r: httpx.Response) -> str:
    try:
        e = r.json().get("error", {})
        return f"[{r.status_code}] {e.get('message', r.text[:120])}"
    except ValueError:
        return f"[{r.status_code}] {r.text[:120]}"


if __name__ == "__main__":
    sys.exit(main())
