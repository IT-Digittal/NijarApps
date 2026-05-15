"""Módulo de seguridad: hashing de contraseñas, generación y validación de JWT.

Implementa los requisitos del ENS Nivel Medio (RD 311/2022):
- Tokens JWT con expiración configurable
- Hashing de contraseñas con bcrypt (cost factor 12)
- Soporte para OAuth2 con scopes RBAC
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from nijar_dti.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _truncar_72_bytes(password: str) -> str:
    """bcrypt limita la entrada a 72 bytes. Truncar manualmente evita un
    ValueError en bcrypt >= 4 (con passlib < 1.7.5) y mantiene la
    compatibilidad — bcrypt nunca consultó más de 72 bytes igualmente.
    """
    encoded = password.encode("utf-8")
    if len(encoded) <= 72:
        return password
    return encoded[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    return pwd_context.hash(_truncar_72_bytes(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return pwd_context.verify(_truncar_72_bytes(plain_password), hashed_password)


def create_access_token(
    subject: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Genera un JWT de acceso firmado.

    Args:
        subject: identificador único del titular (user_id, normalmente).
        scopes: lista de permisos RBAC asociados al token.
        expires_delta: tiempo de vida personalizado del token.

    Returns:
        Token JWT codificado.
    """
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
        "scopes": scopes or [],
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """Genera un JWT de refresco con vida más larga."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un token JWT.

    Raises:
        JWTError: si el token es inválido o ha expirado.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise JWTError(f"Token inválido o expirado: {exc}") from exc
