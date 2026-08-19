"""Tests de helpers de seguridad: hashing, JWT, decode."""

from __future__ import annotations

from uuid import uuid4

import pytest

from nijar_dti.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswords:
    def test_hash_y_verify(self):
        plain = "ContraseñaSegura#2026"
        h = hash_password(plain)
        assert h != plain
        assert verify_password(plain, h)

    def test_verify_con_password_incorrecto(self):
        h = hash_password("correcto")
        assert not verify_password("incorrecto", h)

    def test_hashes_distintos_misma_password(self):
        # bcrypt usa salt aleatorio → mismos plain dan hashes distintos
        h1 = hash_password("test")
        h2 = hash_password("test")
        assert h1 != h2


class TestJWT:
    def test_access_token_decodificable(self):
        sub = str(uuid4())
        scopes = ["administrador_tic"]
        token = create_access_token(subject=sub, scopes=scopes)
        payload = decode_token(token)
        assert payload["sub"] == sub
        assert payload["type"] == "access"
        assert payload["scopes"] == scopes

    def test_refresh_token_marcado_como_refresh(self):
        sub = str(uuid4())
        token = create_refresh_token(subject=sub)
        payload = decode_token(token)
        assert payload["sub"] == sub
        assert payload["type"] == "refresh"

    def test_decode_token_invalido(self):
        with pytest.raises(Exception):
            decode_token("malformed.token.here")
