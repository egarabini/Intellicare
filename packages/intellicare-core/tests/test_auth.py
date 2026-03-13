from __future__ import annotations

import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from intellicare_core.auth.jwt import verify_token

@pytest.fixture
def rsa_fixture() -> tuple[str, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    numbers = private_key.public_key().public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")

    from jose.utils import base64url_encode

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": base64url_encode(n_bytes).decode(),
                "e": base64url_encode(e_bytes).decode(),
            }
        ]
    }
    return private_pem, jwks


@pytest.mark.asyncio
async def test_verify_token_success(
    monkeypatch: pytest.MonkeyPatch, rsa_fixture: tuple[str, dict]
) -> None:
    from intellicare_core.auth import jwt as jwt_module

    private_key, jwks = rsa_fixture
    jwt_module._get_jwks.cache_clear()
    monkeypatch.setattr(jwt_module, "_get_jwks", lambda: jwks)
    monkeypatch.setattr(jwt_module, "_refresh_jwks", lambda: jwks)

    token = jwt.encode(
        {
            "sub": "user-123",
            "tenant_id": "acme",
            "email": "user@test.local",
            "realm_access": {"roles": ["CLINICO"]},
            "exp": int(time.time()) + 600,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )

    ctx = await verify_token(token)
    assert ctx.tenant_id == "acme"
    assert ctx.schema == "tenant_acme"
    assert ctx.has_role("CLINICO")


@pytest.mark.asyncio
async def test_verify_token_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from intellicare_core.auth import jwt as jwt_module

    jwt_module._get_jwks.cache_clear()
    monkeypatch.setattr(jwt_module, "_get_jwks", lambda: {"keys": []})
    monkeypatch.setattr(jwt_module, "_refresh_jwks", lambda: {"keys": []})

    with pytest.raises(HTTPException) as exc:
        await verify_token("bad-token")

    assert exc.value.status_code == 401
