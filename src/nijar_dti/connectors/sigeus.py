"""Cliente de solo lectura de siGEUS (Plataforma Distromel) — RSU y limpieza viaria.

siGEUS es el sistema de gestión de servicios urbanos que usa la contrata de
residuos y limpieza viaria del municipio (contenedores, puntos de recogida,
recogidas por fracción, lavados, papeleras, órdenes de trabajo, flotas y
recursos). Panel web en https://web.sigeus.net; backend REST (.NET) en
https://api.sigeus.net.

Lo que aquí se implementa procede de la configuración pública del panel
(``assets/config/environment.config.json``) y de su bundle Angular, sin
credenciales:

- ``POST api/session/login`` con ``{username, password, applicationCode,
  customerCode, siteCode}`` → ``{token, ...}`` (JWT). ``customerCode`` y
  ``siteCode`` valen ``-1`` para que el servidor asigne los del usuario; si la
  cuenta tiene varias explotaciones se fijan por configuración.
- ``POST api/session/loginOtp`` con ``{username, otp, ...}`` para cuentas con
  segundo factor (no automatizable: pedir al cliente un usuario técnico sin 2FA).
- ``GET Api/Session/RenewToken`` → ``{isAuthenticated, token}``.
- ``GET Api/Session/checkAuthAsync`` y ``GET api/session/user/current``.
- Toda petición autenticada lleva ``Authorization: Bearer <token>`` y las
  cabeceras ``customerCode`` / ``siteCode``, que el panel toma de las
  reclamaciones ``customercode`` / ``sitecode`` del propio JWT.

Los endpoints de negocio (RSU, limpieza viaria, flotas) se cargan en el panel
tras el login y se añaden aquí cuando se disponga de acceso; hasta entonces el
cliente ofrece login con caché de sesión, renovación y ``get``/``post``
genéricos, y las funciones de parseo puras (testeables sin red).

Credenciales en ``SIGEUS_USUARIO`` / ``SIGEUS_PASSWORD``; nunca se versionan.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx

RUTA_LOGIN = "api/session/login"
RUTA_LOGIN_OTP = "api/session/loginOtp"
RUTA_LOGOUT = "api/session/logout"
RUTA_RENOVAR = "Api/Session/RenewToken"
RUTA_COMPROBAR = "Api/Session/checkAuthAsync"
RUTA_USUARIO_ACTUAL = "api/session/user/current"

# Margen de seguridad antes de la caducidad declarada en el JWT (``exp``).
MARGEN_CADUCIDAD_SEGUNDOS = 60
# Vida asumida cuando el token no trae ``exp``: renovamos cada 20 min.
VIDA_POR_DEFECTO_SEGUNDOS = 20 * 60


class SigeusError(RuntimeError):
    """Error de comunicación o autenticación con siGEUS."""


class SigeusRequiere2FAError(SigeusError):
    """La cuenta exige un código OTP: no se puede automatizar el login."""


# --------------------------- Parseo puro (sin red) ---------------------------


def decodificar_claims(token: str) -> dict[str, Any]:
    """Reclamaciones del payload de un JWT **sin verificar la firma**.

    Solo se usa para leer ``customercode`` / ``sitecode`` / ``exp`` del token
    que el propio siGEUS nos ha emitido (igual que hace su panel). Devuelve
    ``{}`` si el token no tiene forma de JWT o el payload no es JSON.
    """
    partes = token.split(".")
    if len(partes) != 3:
        return {}
    payload = partes[1].replace("-", "+").replace("_", "/")
    payload += "=" * (-len(payload) % 4)
    try:
        datos = json.loads(base64.b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _entero(valor: Any) -> int | None:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def construir_cuerpo_login(
    usuario: str,
    password: str,
    application_code: str,
    customer_code: int = -1,
    site_code: int = -1,
) -> dict[str, Any]:
    """Cuerpo exacto que envía el panel a ``api/session/login``."""
    return {
        "customerCode": customer_code,
        "siteCode": site_code,
        "username": usuario,
        "password": password,
        "applicationCode": application_code,
    }


def parsear_respuesta_login(datos: Any) -> str:
    """Extrae el token de la respuesta del login.

    Lanza ``SigeusRequiere2FAError`` si el servidor pide un OTP (la respuesta
    no trae token y marca el segundo factor) y ``SigeusError`` si no hay token.
    """
    if not isinstance(datos, dict):
        raise SigeusError("Respuesta de login inesperada (no es un objeto JSON)")
    token = datos.get("token")
    if isinstance(token, str) and token:
        return token
    marcas_2fa = ("requiresOtp", "requires2FA", "twoFactorRequired", "otpRequired")
    codigo, mensaje = parsear_error_backend(datos)
    if any(bool(datos.get(m)) for m in marcas_2fa) or _es_error_2fa(codigo):
        raise SigeusRequiere2FAError(
            "La cuenta de siGEUS exige segundo factor (OTP); solicitar usuario técnico sin 2FA"
        )
    detalle = mensaje or "credenciales rechazadas"
    if codigo:
        detalle = f"{detalle} [{codigo}]"
    raise SigeusError(f"Login en siGEUS sin token: {detalle}")


def parsear_error_backend(datos: Any) -> tuple[str | None, str | None]:
    """Código y mensaje del formato de error de validación del backend.

    siGEUS responde 400 con ``{"errors": [{"errorCode": "error.code.login.credentials",
    "errorMessage": "...", ...}], "exceptionType": "ValidationError"}``. Devuelve
    ``(codigo, mensaje)`` del primer error, o ``(None, None)`` si no encaja.
    """
    if not isinstance(datos, dict):
        return None, None
    errores = datos.get("errors")
    if isinstance(errores, list) and errores and isinstance(errores[0], dict):
        primero = errores[0]
        codigo = primero.get("errorCode")
        mensaje = primero.get("errorMessage")
        return (str(codigo) if codigo else None, str(mensaje) if mensaje else None)
    mensaje = datos.get("message") or datos.get("errorMessage") or datos.get("error")
    return None, (str(mensaje) if mensaje else None)


def _es_error_2fa(codigo: str | None) -> bool:
    return bool(codigo) and any(m in str(codigo).lower() for m in ("otp", "2fa", "twofactor"))


def cabeceras_autenticadas(
    token: str, customer_code: int | None = None, site_code: int | None = None
) -> dict[str, str]:
    """Cabeceras que espera el backend en cada llamada autenticada.

    ``customerCode`` / ``siteCode`` se toman de las reclamaciones del JWT
    (``customercode`` / ``sitecode``) salvo que se fuercen por configuración.
    """
    claims = decodificar_claims(token)
    cc = customer_code if customer_code is not None else _entero(claims.get("customercode"))
    sc = site_code if site_code is not None else _entero(claims.get("sitecode"))
    cabeceras = {"Authorization": f"Bearer {token}"}
    if cc is not None:
        cabeceras["customerCode"] = str(cc)
    if sc is not None:
        cabeceras["siteCode"] = str(sc)
    return cabeceras


def caducidad_token(token: str, ahora: float | None = None) -> float:
    """Instante (``time.time()``) hasta el que consideramos válido el token.

    Usa ``exp`` del JWT menos un margen; sin ``exp`` asume la vida por defecto.
    """
    ahora = time.time() if ahora is None else ahora
    exp = _entero(decodificar_claims(token).get("exp"))
    if exp is None:
        return ahora + VIDA_POR_DEFECTO_SEGUNDOS
    return max(float(exp) - MARGEN_CADUCIDAD_SEGUNDOS, ahora)


# ------------------------------- Cliente REST -------------------------------


class ClienteSigeus:
    """Cliente REST mínimo (login + sesión cacheada + ``get``/``post`` genéricos)."""

    def __init__(
        self,
        usuario: str,
        password: str,
        base_url: str = "https://api.sigeus.net",
        application_code: str = "0005",
        customer_code: int = -1,
        site_code: int = -1,
        timeout_seconds: int = 12,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._usuario = usuario
        self._password = password
        self._application_code = application_code
        # -1 = «los del usuario»; si se fijan (>= 0) se envían también en cabecera.
        self._customer_code = customer_code
        self._site_code = site_code
        self._timeout = timeout_seconds
        self._token: str | None = None
        self._token_caduca = 0.0

    # ----------------------------------------------------------------- sesión
    def _url(self, ruta: str) -> str:
        return f"{self._base}/{ruta.lstrip('/')}"

    def _cabeceras(self, token: str) -> dict[str, str]:
        return cabeceras_autenticadas(
            token,
            self._customer_code if self._customer_code >= 0 else None,
            self._site_code if self._site_code >= 0 else None,
        )

    def _guardar_token(self, token: str) -> str:
        self._token = token
        self._token_caduca = caducidad_token(token)
        return token

    async def _login(self, client: httpx.AsyncClient) -> str:
        cuerpo = construir_cuerpo_login(
            self._usuario,
            self._password,
            self._application_code,
            self._customer_code,
            self._site_code,
        )
        try:
            resp = await client.post(self._url(RUTA_LOGIN), json=cuerpo)
        except httpx.HTTPError as exc:
            raise SigeusError(f"Login en siGEUS fallido: {exc}") from exc
        datos: Any = None
        try:
            datos = resp.json()
        except ValueError:
            datos = None
        if resp.status_code in (400, 401, 403) and datos is not None:
            # Credenciales rechazadas / OTP: el backend lo explica en el cuerpo.
            return self._guardar_token(parsear_respuesta_login(datos))
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SigeusError(f"Login en siGEUS fallido: {exc}") from exc
        if datos is None:
            raise SigeusError("Login en siGEUS: respuesta no es JSON")
        return self._guardar_token(parsear_respuesta_login(datos))

    async def _renovar(self, client: httpx.AsyncClient, token: str) -> str | None:
        """Intenta ``RenewToken``; devuelve el nuevo token o ``None`` si no procede."""
        try:
            resp = await client.get(self._url(RUTA_RENOVAR), headers=self._cabeceras(token))
            resp.raise_for_status()
            datos = resp.json()
        except (httpx.HTTPError, ValueError):
            return None
        if isinstance(datos, dict) and datos.get("isAuthenticated") and datos.get("token"):
            return self._guardar_token(str(datos["token"]))
        return None

    async def _obtener_token(self, client: httpx.AsyncClient) -> str:
        """Token JWT con caché; renueva antes de caducar y relogea si no puede."""
        if self._token and time.time() < self._token_caduca:
            return self._token
        if self._token:
            renovado = await self._renovar(client, self._token)
            if renovado:
                return renovado
            self._token = None
        return await self._login(client)

    def cerrar_sesion_local(self) -> None:
        """Olvida el token cacheado (fuerza un login en la siguiente llamada)."""
        self._token = None
        self._token_caduca = 0.0

    # --------------------------------------------------------------- llamadas
    async def _llamar(
        self,
        metodo: str,
        ruta: str,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            token = await self._obtener_token(client)
            try:
                resp = await client.request(
                    metodo,
                    self._url(ruta),
                    params=params,
                    json=json_body,
                    headers=self._cabeceras(token),
                )
                if resp.status_code == 401:  # token revocado: relogin y un reintento
                    self.cerrar_sesion_local()
                    token = await self._obtener_token(client)
                    resp = await client.request(
                        metodo,
                        self._url(ruta),
                        params=params,
                        json=json_body,
                        headers=self._cabeceras(token),
                    )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise SigeusError(f"{metodo} {ruta} fallido: {exc}") from exc
            if not resp.content:
                return None
            try:
                return resp.json()
            except ValueError as exc:
                raise SigeusError(f"{metodo} {ruta}: respuesta no es JSON") from exc

    async def get(self, ruta: str, params: dict[str, Any] | None = None) -> Any:
        """GET autenticado a una ruta relativa (p. ej. ``api/session/user/current``)."""
        return await self._llamar("GET", ruta, params=params)

    async def post(self, ruta: str, json_body: Any | None = None) -> Any:
        """POST autenticado (el backend usa POST también para listados ``GetListAsync``)."""
        return await self._llamar("POST", ruta, json_body=json_body)

    async def comprobar_sesion(self) -> bool:
        """``checkAuthAsync``: True si el backend acepta la sesión actual."""
        datos = await self.get(RUTA_COMPROBAR)
        if isinstance(datos, dict):
            return bool(datos.get("isAuthenticated", True))
        return bool(datos)

    async def usuario_actual(self) -> dict[str, Any]:
        """Perfil del usuario con el que se ha iniciado sesión."""
        datos = await self.get(RUTA_USUARIO_ACTUAL)
        return dict(datos) if isinstance(datos, dict) else {}

    def claims_sesion(self) -> dict[str, Any]:
        """Reclamaciones del token en caché (``customercode``, ``sitecode``, ``exp``...)."""
        return decodificar_claims(self._token) if self._token else {}
