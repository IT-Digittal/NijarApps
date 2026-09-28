"""Tests del conector siGEUS (Distromel · RSU y limpieza viaria): parseo puro, sin red.

Los fixtures reproducen el contrato del panel web.sigeus.net (cuerpo del login,
JWT con ``customercode``/``sitecode`` y respuesta de ``RenewToken``).
"""

from __future__ import annotations

import base64
import json
import time

import pytest

from nijar_dti.config import Settings
from nijar_dti.connectors.sigeus import (
    MARGEN_CADUCIDAD_SEGUNDOS,
    RUTA_LOGIN,
    RUTA_LOGIN_OTP,
    RUTA_RENOVAR,
    VIDA_POR_DEFECTO_SEGUNDOS,
    ClienteSigeus,
    SigeusError,
    SigeusRequiere2FAError,
    cabeceras_autenticadas,
    caducidad_token,
    construir_cuerpo_login,
    construir_cuerpo_login_otp,
    decodificar_claims,
    generar_totp,
    modo_segundo_factor,
    parsear_error_backend,
    parsear_respuesta_login,
)
from nijar_dti.data.seeds.fuentes_datos import FUENTES_DATOS_SEED
from nijar_dti.schemas.gemelo import EstadoGemelo
from nijar_dti.services.sigeus_service import sigeus_configurado


def _jwt(claims: dict) -> str:
    def b64(obj: dict) -> str:
        raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{b64({'alg': 'HS256', 'typ': 'JWT'})}.{b64(claims)}.firma"


TOKEN = _jwt({"sub": "tecnico", "customercode": "17", "sitecode": "3", "exp": 4_102_444_800})


class TestParseoPuro:
    def test_rutas_coinciden_con_el_panel(self):
        # Las rutas salen de assets/config/environment.config.json del panel
        assert RUTA_LOGIN == "api/session/login"
        assert RUTA_LOGIN_OTP == "api/session/loginOtp"
        assert RUTA_RENOVAR == "Api/Session/RenewToken"

    def test_cuerpo_login_como_el_panel(self):
        cuerpo = construir_cuerpo_login("tecnico", "secreto", "0005")
        assert cuerpo == {
            "customerCode": -1,
            "siteCode": -1,
            "username": "tecnico",
            "password": "secreto",
            "applicationCode": "0005",
        }
        assert construir_cuerpo_login("u", "p", "0005", 17, 3)["customerCode"] == 17

    def test_decodificar_claims_jwt_url_safe(self):
        claims = decodificar_claims(TOKEN)
        assert claims["customercode"] == "17" and claims["sitecode"] == "3"
        # Token con payload que necesita relleno base64 y caracteres '-' / '_'
        raro = _jwt({"x": "¿¿??>>", "customercode": 1})
        assert decodificar_claims(raro)["customercode"] == 1

    def test_decodificar_claims_tolerante(self):
        assert decodificar_claims("") == {}
        assert decodificar_claims("no-es-un-jwt") == {}
        assert decodificar_claims("a.b.c") == {}
        assert decodificar_claims("a." + base64.urlsafe_b64encode(b"[1]").decode() + ".c") == {}

    def test_parsear_respuesta_login_devuelve_token(self):
        assert parsear_respuesta_login({"token": TOKEN, "isAuthenticated": True}) == TOKEN

    def test_parsear_respuesta_login_detecta_2fa(self):
        with pytest.raises(SigeusRequiere2FAError):
            parsear_respuesta_login({"token": None, "requiresOtp": True})

    def test_parsear_respuesta_login_2fa_formato_real(self):
        # Cuerpo real (HTTP 200) de api.sigeus.net con una cuenta con segundo
        # factor: token nulo y ``twoFactorAuthentication: true``.
        cuerpo = {
            "token": None,
            "twoFactorAuthentication": True,
            "twoFactorAuthenticationMode": 0,
            "passwordExpired": False,
            "trustedDeviceCookie": None,
        }
        with pytest.raises(SigeusRequiere2FAError):
            parsear_respuesta_login(cuerpo)
        # Sin segundo factor activo el mismo formato es un login sin token.
        with pytest.raises(SigeusError, match="credenciales rechazadas"):
            parsear_respuesta_login({"token": None, "twoFactorAuthentication": False})

    def test_parsear_respuesta_login_sin_token(self):
        with pytest.raises(SigeusError, match="credenciales rechazadas"):
            parsear_respuesta_login({"token": ""})
        with pytest.raises(SigeusError, match="Usuario bloqueado"):
            parsear_respuesta_login({"message": "Usuario bloqueado"})
        with pytest.raises(SigeusError):
            parsear_respuesta_login("texto plano")

    def test_parsear_error_backend_formato_real(self):
        # Cuerpo real (HTTP 400) de api.sigeus.net ante credenciales incorrectas
        cuerpo = {
            "errors": [
                {
                    "propertyName": "",
                    "errorMessage": "'' no cumple con la condición especificada.",
                    "attemptedValue": {"userName": "prueba", "password": "****"},
                    "errorCode": "error.code.login.credentials",
                }
            ],
            "exceptionType": "ValidationError",
        }
        assert parsear_error_backend(cuerpo) == (
            "error.code.login.credentials",
            "'' no cumple con la condición especificada.",
        )
        with pytest.raises(SigeusError, match=r"error\.code\.login\.credentials"):
            parsear_respuesta_login(cuerpo)
        assert parsear_error_backend({"message": "caído"}) == (None, "caído")
        assert parsear_error_backend({"errors": []}) == (None, None)
        assert parsear_error_backend("x") == (None, None)

    def test_error_backend_con_codigo_otp_es_2fa(self):
        cuerpo = {"errors": [{"errorCode": "error.code.login.otpRequired"}]}
        with pytest.raises(SigeusRequiere2FAError):
            parsear_respuesta_login(cuerpo)

    def test_cabeceras_toman_explotacion_del_jwt(self):
        cab = cabeceras_autenticadas(TOKEN)
        assert cab == {
            "Authorization": f"Bearer {TOKEN}",
            "customerCode": "17",
            "siteCode": "3",
        }

    def test_cabeceras_forzadas_por_configuracion(self):
        cab = cabeceras_autenticadas(TOKEN, customer_code=99, site_code=5)
        assert cab["customerCode"] == "99" and cab["siteCode"] == "5"

    def test_cabeceras_sin_explotacion_en_el_token(self):
        cab = cabeceras_autenticadas(_jwt({"sub": "x"}))
        assert cab == {"Authorization": f"Bearer {_jwt({'sub': 'x'})}"}

    def test_caducidad_usa_exp_con_margen(self):
        ahora = 1_000_000.0
        token = _jwt({"exp": int(ahora) + 3600})
        assert caducidad_token(token, ahora) == ahora + 3600 - MARGEN_CADUCIDAD_SEGUNDOS

    def test_caducidad_sin_exp_asume_vida_por_defecto(self):
        ahora = 1_000_000.0
        assert caducidad_token(_jwt({"sub": "x"}), ahora) == ahora + VIDA_POR_DEFECTO_SEGUNDOS
        # exp ya pasado → caduca «ahora», nunca en el pasado
        assert caducidad_token(_jwt({"exp": 1}), ahora) == ahora


class TestClienteSinRed:
    def test_url_y_cabeceras_del_cliente(self):
        c = ClienteSigeus("u", "p", base_url="https://api.sigeus.net/")
        assert c._url("api/session/login") == "https://api.sigeus.net/api/session/login"
        assert c._url("/Api/Session/RenewToken") == "https://api.sigeus.net/Api/Session/RenewToken"
        c._guardar_token(TOKEN)
        assert c.claims_sesion()["customercode"] == "17"
        assert c._cabeceras(TOKEN)["customerCode"] == "17"
        assert c._token_caduca > time.time()

    def test_codigos_negativos_no_se_fuerzan_en_cabecera(self):
        c = ClienteSigeus("u", "p", customer_code=-1, site_code=-1)
        assert c._cabeceras(_jwt({"sub": "x"})) == {"Authorization": f"Bearer {_jwt({'sub': 'x'})}"}
        forzado = ClienteSigeus("u", "p", customer_code=4, site_code=0)
        cab = forzado._cabeceras(_jwt({"sub": "x"}))
        assert cab["customerCode"] == "4" and cab["siteCode"] == "0"

    def test_cerrar_sesion_local(self):
        c = ClienteSigeus("u", "p")
        c._guardar_token(TOKEN)
        c.cerrar_sesion_local()
        assert c.claims_sesion() == {} and c._token_caduca == 0.0

    async def test_obtener_token_reutiliza_cache(self):
        c = ClienteSigeus("u", "p")
        c._guardar_token(TOKEN)
        assert await c._obtener_token(client=None) == TOKEN  # type: ignore[arg-type]

    async def test_obtener_token_renueva_antes_de_caducar(self, monkeypatch):
        c = ClienteSigeus("u", "p")
        c._token = TOKEN
        c._token_caduca = 0.0  # caducado → primero RenewToken, sin relogin
        nuevo = _jwt({"customercode": "17", "sitecode": "3", "exp": 4_102_444_800, "n": 2})

        async def renovar(client, token):
            assert token == TOKEN
            return c._guardar_token(nuevo)

        async def login(client):  # pragma: no cover - no debe llamarse
            raise AssertionError("no debe relogear si la renovación funciona")

        monkeypatch.setattr(c, "_renovar", renovar)
        monkeypatch.setattr(c, "_login", login)
        assert await c._obtener_token(client=None) == nuevo  # type: ignore[arg-type]

    async def test_obtener_token_relogea_si_no_renueva(self, monkeypatch):
        c = ClienteSigeus("u", "p")
        c._token = TOKEN
        c._token_caduca = 0.0

        async def renovar(client, token):
            return None

        async def login(client):
            return c._guardar_token(TOKEN)

        monkeypatch.setattr(c, "_renovar", renovar)
        monkeypatch.setattr(c, "_login", login)
        assert await c._obtener_token(client=None) == TOKEN  # type: ignore[arg-type]


@pytest.fixture()
def sin_entorno_sigeus(monkeypatch):
    """Aísla los tests de la configuración real (variables SIGEUS_* del entorno)."""
    for clave in (
        "SIGEUS_BASE_URL",
        "SIGEUS_USUARIO",
        "SIGEUS_PASSWORD",
        "SIGEUS_TOTP_SECRET",
        "SIGEUS_APPLICATION_CODE",
        "SIGEUS_CUSTOMER_CODE",
        "SIGEUS_SITE_CODE",
        "SIGEUS_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(clave, raising=False)


@pytest.mark.usefixtures("sin_entorno_sigeus")
class TestConfiguracion:
    def test_valores_por_defecto_del_panel(self):
        s = Settings()
        assert s.sigeus_base_url == "https://api.sigeus.net"
        assert s.sigeus_application_code == "0005"
        assert s.sigeus_customer_code == -1 and s.sigeus_site_code == -1
        assert s.sigeus_timeout_seconds == 12

    def test_sigeus_configurado_segun_settings(self):
        assert not sigeus_configurado(Settings())  # sin credenciales → apagado
        assert sigeus_configurado(Settings(sigeus_usuario="tecnico", sigeus_password="s"))
        assert not sigeus_configurado(Settings(sigeus_usuario="tecnico"))
        assert not sigeus_configurado(
            Settings(sigeus_usuario="t", sigeus_password="s", sigeus_base_url="")
        )

    def test_estado_gemelo_incluye_sigeus(self):
        assert EstadoGemelo(thingsboard_configurado=False).sigeus_configurado is False


class TestCatalogoFuentes:
    def test_fd116_en_el_catalogo(self):
        fd = next(f for f in FUENTES_DATOS_SEED if f["codigo"] == "FD-116")
        assert fd["origen"] == "externa" and fd["estado"] == "pendiente_acceso"
        assert fd["categoria"] == "residuos" and fd["requiere_credenciales"]
        assert "sigeus" in fd["sistema"].lower()
        assert "SIGEUS_USUARIO" in fd["credenciales_desc"]
        assert "verificar_sigeus" in fd["notas"]


# Secreto de los vectores de prueba del RFC 6238 («12345678901234567890» en base32).
SECRETO_RFC6238 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


class TestSegundoFactor:
    @pytest.mark.parametrize(
        ("instante", "esperado"),
        [(59, "287082"), (1111111109, "081804"), (1111111111, "050471"), (1234567890, "005924")],
    )
    def test_generar_totp_vectores_rfc6238(self, instante, esperado):
        assert generar_totp(SECRETO_RFC6238, instante) == esperado

    def test_generar_totp_admite_secreto_con_espacios_y_minusculas(self):
        assert generar_totp("gezd gnbv gy3t qojq gezd gnbv gy3t qojq", 59) == "287082"

    def test_generar_totp_secreto_invalido(self):
        with pytest.raises(SigeusError, match="base32"):
            generar_totp("no-es-base32!!", 59)
        with pytest.raises(SigeusError):
            generar_totp("", 59)

    def test_modo_segundo_factor(self):
        assert modo_segundo_factor({"twoFactorAuthenticationMode": "TOTP"}) == "TOTP"
        assert modo_segundo_factor({"twoFactorAuthenticationMode": "otp"}) == "OTP"
        assert modo_segundo_factor({"twoFactorAuthenticationMode": 2}) == "TOTP"
        assert modo_segundo_factor({"twoFactorAuthenticationMode": 1}) == "OTP"
        assert modo_segundo_factor({"twoFactorAuthentication": True}) is None
        assert modo_segundo_factor("x") is None

    def test_respuesta_real_modo_cero_es_correo(self):
        # Respuesta real de api.sigeus.net con la cuenta facilitada (HTTP 200)
        real = {
            "token": None,
            "twoFactorAuthentication": True,
            "twoFactorAuthenticationMode": 0,
            "passwordExpired": False,
            "trustedDeviceCookie": None,
        }
        assert modo_segundo_factor(real) == "OTP"
        with pytest.raises(SigeusRequiere2FAError) as exc:
            parsear_respuesta_login(real)
        assert exc.value.modo == "OTP" and "correo" in str(exc.value)
        # Sin segundo factor activo, el 0 no significa nada
        assert modo_segundo_factor({"twoFactorAuthenticationMode": 0}) is None

    def test_respuesta_2fa_real_lleva_el_modo(self):
        # Respuesta real observada: HTTP 200 con token nulo y la marca de segundo factor
        with pytest.raises(SigeusRequiere2FAError) as exc:
            parsear_respuesta_login(
                {
                    "token": None,
                    "twoFactorAuthentication": True,
                    "twoFactorAuthenticationMode": "TOTP",
                }
            )
        assert exc.value.modo == "TOTP" and "SIGEUS_TOTP_SECRET" in str(exc.value)
        with pytest.raises(SigeusRequiere2FAError) as exc2:
            parsear_respuesta_login(
                {
                    "token": None,
                    "twoFactorAuthentication": True,
                    "twoFactorAuthenticationMode": "OTP",
                }
            )
        assert exc2.value.modo == "OTP" and "correo" in str(exc2.value)

    def test_cuerpo_login_otp_como_el_panel(self):
        cuerpo = construir_cuerpo_login_otp("tecnico", "123456", "0005", 10201, 103)
        assert cuerpo["otp"] == "123456" and cuerpo["username"] == "tecnico"
        assert cuerpo["customerCode"] == 10201 and cuerpo["siteCode"] == 103
        assert cuerpo["applicationCode"] == "0005" and cuerpo["isTrustedDevice"] is False
        assert cuerpo["userAgent"]

    async def test_login_completa_el_segundo_paso_con_totp(self, monkeypatch):
        c = ClienteSigeus(
            "tecnico", "p", customer_code=10201, site_code=103, totp_secret=SECRETO_RFC6238
        )
        llamadas: list[tuple[str, dict]] = []

        async def post_sesion(client, ruta, cuerpo):
            llamadas.append((ruta, cuerpo))
            if ruta == RUTA_LOGIN:
                return {
                    "token": None,
                    "twoFactorAuthentication": True,
                    "twoFactorAuthenticationMode": "TOTP",
                }
            assert ruta == RUTA_LOGIN_OTP
            assert (
                cuerpo["otp"] == generar_totp(SECRETO_RFC6238) and cuerpo["username"] == "tecnico"
            )
            return {"token": TOKEN, "isAuthenticated": True}

        monkeypatch.setattr(c, "_post_sesion", post_sesion)
        assert await c._login(client=None) == TOKEN  # type: ignore[arg-type]
        assert [r for r, _ in llamadas] == [RUTA_LOGIN, RUTA_LOGIN_OTP]

    async def test_login_sin_secreto_eleva_2fa(self, monkeypatch):
        c = ClienteSigeus("tecnico", "p")

        async def post_sesion(client, ruta, cuerpo):
            return {
                "token": None,
                "twoFactorAuthentication": True,
                "twoFactorAuthenticationMode": "TOTP",
            }

        monkeypatch.setattr(c, "_post_sesion", post_sesion)
        with pytest.raises(SigeusRequiere2FAError) as exc:
            await c._login(client=None)  # type: ignore[arg-type]
        assert exc.value.modo == "TOTP"

    async def test_login_por_correo_no_usa_totp(self, monkeypatch):
        c = ClienteSigeus("tecnico", "p", totp_secret=SECRETO_RFC6238)
        rutas: list[str] = []

        async def post_sesion(client, ruta, cuerpo):
            rutas.append(ruta)
            return {
                "token": None,
                "twoFactorAuthentication": True,
                "twoFactorAuthenticationMode": "OTP",
            }

        monkeypatch.setattr(c, "_post_sesion", post_sesion)
        with pytest.raises(SigeusRequiere2FAError):
            await c._login(client=None)  # type: ignore[arg-type]
        assert rutas == [RUTA_LOGIN]  # no se intenta loginOtp con un código que no tenemos

    async def test_totp_rechazado_da_error_claro(self, monkeypatch):
        c = ClienteSigeus("tecnico", "p", totp_secret=SECRETO_RFC6238)

        async def post_sesion(client, ruta, cuerpo):
            if ruta == RUTA_LOGIN:
                return {"token": None, "twoFactorAuthentication": True}
            return {"token": None, "twoFactorAuthentication": True}

        monkeypatch.setattr(c, "_post_sesion", post_sesion)
        with pytest.raises(SigeusError, match="rechazó el código TOTP"):
            await c._login(client=None)  # type: ignore[arg-type]

    def test_settings_totp_por_defecto_vacio(self, sin_entorno_sigeus):
        assert Settings().sigeus_totp_secret == ""
