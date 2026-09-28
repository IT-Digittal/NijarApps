"""Servicio de la integración siGEUS (Distromel): RSU y limpieza viaria.

Encapsula la configuración y el cliente único del conector. Los KPIs de
negocio (contenedores, recogidas, papeleras, órdenes de trabajo, flotas) se
incorporan aquí cuando se disponga de acceso y se hayan capturado los
endpoints reales del panel; mientras tanto, expone el estado de configuración
y una comprobación de sesión para el verificador.
"""

from __future__ import annotations

from typing import Any

from nijar_dti.config import Settings, get_settings
from nijar_dti.connectors.sigeus import ClienteSigeus

_cliente: ClienteSigeus | None = None


def sigeus_configurado(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return bool(s.sigeus_base_url and s.sigeus_usuario and s.sigeus_password)


def _obtener_cliente() -> ClienteSigeus:
    global _cliente
    if _cliente is None:
        s = get_settings()
        _cliente = ClienteSigeus(
            usuario=s.sigeus_usuario,
            password=s.sigeus_password,
            base_url=s.sigeus_base_url,
            application_code=s.sigeus_application_code,
            customer_code=s.sigeus_customer_code,
            site_code=s.sigeus_site_code,
            timeout_seconds=s.sigeus_timeout_seconds,
            totp_secret=s.sigeus_totp_secret,
        )
    return _cliente


async def comprobar_acceso() -> dict[str, Any]:
    """Inicia sesión y devuelve el perfil del usuario y los códigos de explotación.

    Lanza ``SigeusError`` (o ``SigeusRequiere2FAError``) si no se puede entrar.
    """
    cliente = _obtener_cliente()
    usuario = await cliente.usuario_actual()
    claims = cliente.claims_sesion()
    return {
        "usuario": usuario,
        "customer_code": claims.get("customercode"),
        "site_code": claims.get("sitecode"),
        "sesion_valida": await cliente.comprobar_sesion(),
    }
