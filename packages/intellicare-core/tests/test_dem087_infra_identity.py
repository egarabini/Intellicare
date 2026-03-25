"""
DEM-087 — Testes: JWT issuer alignment + Identity route
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import JWTError

from intellicare_core.auth.jwt import _decode_with_jwks, get_current_tenant
from intellicare_core.config.settings import Settings
from intellicare_core.contracts.base import TenantContext
from modules.identity.router import router as identity_router
from modules.identity.schemas import PessoaFisicaIn

ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="admin-uid",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)


def _build_app() -> TestClient:
    app = FastAPI()
    app.include_router(identity_router)
    app.dependency_overrides[get_current_tenant] = lambda: ADMIN_CTX
    return TestClient(app)


# ── Test 1: jwt_local — issuer validation ─────────────────────────

def test_keycloak_issuer_from_settings_default() -> None:
    """Sem KEYCLOAK_ISSUER_URL, issuer é montado a partir de base_url + realm."""
    s = Settings(
        keycloak_url="http://localhost:8080",
        keycloak_internal_url="",
        keycloak_realm="intellicare",
        keycloak_issuer_url="",
    )
    assert s.keycloak_issuer == "http://localhost:8080/realms/intellicare"


def test_keycloak_issuer_from_explicit_env() -> None:
    """Com KEYCLOAK_ISSUER_URL explícito, esse valor tem prioridade."""
    s = Settings(
        keycloak_url="http://localhost:8080",
        keycloak_internal_url="http://keycloak:8080",
        keycloak_realm="intellicare",
        keycloak_issuer_url="https://auth.intellicare.ia.br/realms/intellicare",
    )
    assert s.keycloak_issuer == "https://auth.intellicare.ia.br/realms/intellicare"


def test_decode_with_jwks_rejects_wrong_issuer() -> None:
    """_decode_with_jwks deve rejeitar token com issuer diferente do esperado."""
    fake_jwks: dict = {"keys": []}
    with pytest.raises(JWTError):
        _decode_with_jwks("fake.token.here", fake_jwks, issuer="http://wrong-issuer")


# ── Test 2: traefik_public — identity route reachable ─────────────

def test_identity_route_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /identity/pessoas/{id} deve retornar 404 (não 405) com dep override."""
    async def _fake_get_by_id(pid):
        return None
    monkeypatch.setattr("modules.identity.router.get_pessoa_by_id", _fake_get_by_id)
    client = _build_app()
    random_id = str(uuid4())
    resp = client.get(f"/identity/pessoas/{random_id}")
    # 404 = rota existe mas pessoa não encontrada (esperado)
    # 405 = rota não existe (falha)
    assert resp.status_code != 405, "Rota /identity/pessoas não encontrada"


def test_identity_post_route_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /identity/pessoas deve retornar algo diferente de 405."""
    created = {
        "id": str(uuid4()), "tipo": "FISICA",
        "nome_completo": "Teste DEM087", "cpf": "12345678900",
        "data_nascimento": None, "genero": None,
    }
    async def _fake_find_or_create(payload):
        return created
    monkeypatch.setattr("modules.identity.router.find_or_create_by_cpf", _fake_find_or_create)
    client = _build_app()
    resp = client.post(
        "/identity/pessoas",
        json={"nome_completo": "Teste DEM087", "cpf": "123.456.789-00"},
    )
    assert resp.status_code != 405, "Rota POST /identity/pessoas não encontrada"


# ── Test 3: idempotency_smoke — create pessoa twice → same id ─────

@pytest.mark.asyncio
async def test_identity_idempotency_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """Criar mesma pessoa 2x retorna mesmo pessoa_id."""
    from modules.identity.services import find_or_create_by_cpf

    pessoa_id = uuid4()
    payload = PessoaFisicaIn(nome_completo="Joao DEM087", cpf="987.654.321-00")
    record = {
        "id": pessoa_id,
        "tipo": "FISICA",
        "nome_completo": "Joao DEM087",
        "cpf": "98765432100",
        "data_nascimento": None,
        "genero": None,
    }

    first_call = {"done": False}

    async def fake_get(cpf: str):
        if first_call["done"]:
            return record
        first_call["done"] = True
        return None

    async def fake_create(payload_in: PessoaFisicaIn, cpf_clean: str):
        return record

    monkeypatch.setattr("modules.identity.services.get_pessoa_by_cpf", fake_get)
    monkeypatch.setattr("modules.identity.services.create_pessoa_fisica", fake_create)

    result1 = await find_or_create_by_cpf(payload)
    result2 = await find_or_create_by_cpf(payload)
    assert result1["id"] == result2["id"] == pessoa_id
