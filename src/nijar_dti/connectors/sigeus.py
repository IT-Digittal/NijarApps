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
  segundo factor. El login responde ``{"token": null,
  "twoFactorAuthentication": true, "twoFactorAuthenticationMode": "OTP"|"TOTP"}``:
  ``OTP`` es un código enviado por correo (no automatizable) y ``TOTP`` un
  código de aplicación autenticadora (RFC 6238), que este cliente genera si se
  configura ``SIGEUS_TOTP_SECRET`` con el secreto en base32 de la cuenta.
- ``GET Api/Session/RenewToken`` → ``{isAuthenticated, token}``.
- ``GET Api/Session/checkAuthAsync`` y ``GET api/session/user/current``.
- Toda petición autenticada lleva ``Authorization: Bearer <token>`` y las
  cabeceras ``customerCode`` / ``siteCode``, que el panel toma de las
  reclamaciones ``customercode`` / ``sitecode`` del propio JWT.

Los endpoints de negocio (RSU, limpieza viaria, flotas) se cargan en el panel
tras el login y se añaden aquí cuando se disponga de acceso; hasta entonces el
cliente ofrece login con caché de sesión, renovación y ``get``/``post``
genéricos, y las funciones de parseo puras (testeables sin red).

Credenciales en ``SIGEUS_USUARIO`` / ``SIGEUS_PASSWORD`` (y ``SIGEUS_TOTP_SECRET``
si la cuenta usa autenticador); nunca se versionan.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
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
# Modos de segundo factor que devuelve el backend en ``twoFactorAuthenticationMode``.
MODO_2FA_CORREO = "OTP"  # código enviado por correo electrónico
MODO_2FA_AUTENTICADOR = "TOTP"  # código de aplicación autenticadora (RFC 6238)
# Identificador de dispositivo que se envía en ``loginOtp`` (el panel manda el user-agent).
USER_AGENT_OTP = "nijar-dti-sigeus/1.0"


class SigeusError(RuntimeError):
    """Error de comunicación o autenticación con siGEUS."""


class SigeusRequiere2FAError(SigeusError):
    """La cuenta exige segundo factor y no se ha podido resolver automáticamente.

    ``modo`` es ``"OTP"`` (código por correo), ``"TOTP"`` (autenticador) o
    ``None`` si el backend no lo indica.
    """

    def __init__(self, mensaje: str, modo: str | None = None) -> None:
        super().__init__(mensaje)
        self.modo = modo


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
    # ``twoFactorAuthentication`` es la marca real del backend (HTTP 200 con
    # ``token: null`` cuando la cuenta tiene segundo factor); el resto se dejan
    # por compatibilidad con otras versiones del panel.
    marcas_2fa = (
        "twoFactorAuthentication",
        "requiresOtp",
        "requires2FA",
        "twoFactorRequired",
        "otpRequired",
    )
    codigo, mensaje = parsear_error_backend(datos)
    if any(bool(datos.get(m)) for m in marcas_2fa) or _es_error_2fa(codigo):
        modo = modo_segundo_factor(datos)
        if modo == MODO_2FA_AUTENTICADOR:
            detalle = (
                "autenticador (TOTP): configurar SIGEUS_TOTP_SECRET con el secreto de la cuenta"
            )
        elif modo == MODO_2FA_CORREO:
            detalle = (
                "código por correo (OTP), no automatizable: cambiar la cuenta a autenticador "
                "(TOTP) o solicitar usuario técnico sin 2FA"
            )
        else:
            detalle = "solicitar usuario técnico sin 2FA o configurar SIGEUS_TOTP_SECRET"
        raise SigeusRequiere2FAError(
            f"La cuenta de siGEUS exige segundo factor · {detalle}", modo=modo
        )
    detalle = mensaje or "credenciales rechazadas"
    if codigo:
        detalle = f"{detalle} [{codigo}]"
    raise SigeusError(f"Login en siGEUS sin token: {detalle}")


def modo_segundo_factor(datos: Any) -> str | None:
    """``"OTP"`` / ``"TOTP"`` según ``twoFactorAuthenticationMode``, o ``None``.

    El backend devuelve el enum numérico ``ETwoFactorMode`` (``None=0``,
    ``OTP=1``, ``TOTP=2``). Respuesta real observada con una cuenta con segundo
    factor por correo: ``{"token": null, "twoFactorAuthentication": true,
    "twoFactorAuthenticationMode": 0, "passwordExpired": false,
    "trustedDeviceCookie": null}``; el panel trata ese ``0`` con el segundo factor
    activo como código por correo (``modo || OTP``), y aquí se hace lo mismo.
    """
    if not isinstance(datos, dict):
        return None
    modo = datos.get("twoFactorAuthenticationMode")
    if isinstance(modo, str) and modo.strip():
        return modo.strip().upper()
    if isinstance(modo, bool):
        return None
    if isinstance(modo, int):
        if modo == 0 and datos.get("twoFactorAuthentication"):
            return MODO_2FA_CORREO
        return {1: MODO_2FA_CORREO, 2: MODO_2FA_AUTENTICADOR}.get(modo)
    return None


def generar_totp(
    secreto_base32: str,
    instante: float | None = None,
    periodo: int = 30,
    digitos: int = 6,
) -> str:
    """Código TOTP (RFC 6238, HMAC-SHA1) para el secreto en base32 de la cuenta.

    Es lo mismo que calcula la aplicación autenticadora; el secreto es el que
    muestra siGEUS al activar el TOTP en el perfil del usuario (junto al QR).
    """
    limpio = "".join(secreto_base32.split()).replace("-", "").upper()
    limpio += "=" * (-len(limpio) % 8)
    try:
        clave = base64.b32decode(limpio, casefold=True)
    except (ValueError, TypeError) as exc:
        raise SigeusError("SIGEUS_TOTP_SECRET no es un secreto base32 válido") from exc
    if not clave:
        raise SigeusError("SIGEUS_TOTP_SECRET está vacío")
    ahora = time.time() if instante is None else instante
    contador = int(ahora // periodo)
    resumen = hmac.new(clave, struct.pack(">Q", contador), hashlib.sha1).digest()
    desplazamiento = resumen[-1] & 0x0F
    numero = struct.unpack(">I", resumen[desplazamiento : desplazamiento + 4])[0] & 0x7FFFFFFF
    return str(numero % (10**digitos)).zfill(digitos)


def construir_cuerpo_login_otp(
    usuario: str,
    otp: str,
    application_code: str,
    customer_code: int = -1,
    site_code: int = -1,
) -> dict[str, Any]:
    """Cuerpo exacto que envía el panel a ``api/session/loginOtp``."""
    return {
        "customerCode": customer_code,
        "siteCode": site_code,
        "username": usuario,
        "otp": otp,
        "applicationCode": application_code,
        "isTrustedDevice": False,
        "userAgent": USER_AGENT_OTP,
    }


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
        totp_secret: str = "",
    ) -> None:
        self._base = base_url.rstrip("/")
        self._usuario = usuario
        self._password = password
        self._totp_secret = totp_secret.strip()
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

    async def _post_sesion(self, client: httpx.AsyncClient, ruta: str, cuerpo: Any) -> Any:
        """POST de login/loginOtp: devuelve el JSON aunque el backend responda 400/401/403."""
        try:
            resp = await client.post(self._url(ruta), json=cuerpo)
        except httpx.HTTPError as exc:
            raise SigeusError(f"Login en siGEUS fallido: {exc}") from exc
        datos: Any = None
        try:
            datos = resp.json()
        except ValueError:
            datos = None
        if resp.status_code in (400, 401, 403) and datos is not None:
            # Credenciales rechazadas / OTP: el backend lo explica en el cuerpo.
            return datos
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SigeusError(f"Login en siGEUS fallido: {exc}") from exc
        if datos is None:
            raise SigeusError("Login en siGEUS: respuesta no es JSON")
        return datos

    async def _login_otp(self, client: httpx.AsyncClient) -> str:
        """Segundo paso del login con el código del autenticador (TOTP)."""
        cuerpo = construir_cuerpo_login_otp(
            self._usuario,
            generar_totp(self._totp_secret),
            self._application_code,
            self._customer_code,
            self._site_code,
        )
        datos = await self._post_sesion(client, RUTA_LOGIN_OTP, cuerpo)
        try:
            return self._guardar_token(parsear_respuesta_login(datos))
        except SigeusRequiere2FAError as exc:
            raise SigeusError(
                "siGEUS rechazó el código TOTP: revisar SIGEUS_TOTP_SECRET y la hora del sistema"
            ) from exc

    async def _login(self, client: httpx.AsyncClient) -> str:
        cuerpo = construir_cuerpo_login(
            self._usuario,
            self._password,
            self._application_code,
            self._customer_code,
            self._site_code,
        )
        datos = await self._post_sesion(client, RUTA_LOGIN, cuerpo)
        try:
            return self._guardar_token(parsear_respuesta_login(datos))
        except SigeusRequiere2FAError as exc:
            if self._totp_secret and exc.modo != MODO_2FA_CORREO:
                return await self._login_otp(client)
            raise

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
