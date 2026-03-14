"""
Fixtures de sessão para testes E2E.
Requerem ambiente rodando: docker-compose up -d
"""
from __future__ import annotations

import os

import httpx
import pytest

# ---------------------------------------------------------------------------
# Configuração de ambiente
# ---------------------------------------------------------------------------
API_URL = os.getenv("E2E_API_URL", "http://localhost:8000")
KC_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KC_REALM = "intellicare"
KC_CLIENT_ID = "intellicare-service"
KC_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")

ADMIN_USER = os.getenv("KEYCLOAK_ADMIN", "admin")
ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

E2E_TENANT_SLUG = "e2e_test"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KC_URL}/realms/{KC_REALM}/protocol/openid-connect/token",
        data={
            "client_id": KC_CLIENT_ID,
            "client_secret": KC_CLIENT_SECRET,
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "openid",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def admin_token() -> str:
    return get_token("platform-admin", "Admin@2025!")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api() -> httpx.Client:
    """Cliente HTTP sincrono apontando para intellicare-service."""
    with httpx.Client(base_url=API_URL, timeout=15) as client:
        yield client


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    return auth_headers(admin_token())


@pytest.fixture(scope="session")
def gestor_headers() -> dict[str, str]:
    """Token do gestor-dev (tenant_dev)."""
    return auth_headers(get_token("gestor-dev", "Gestor@2025!"))


@pytest.fixture(scope="session", autouse=True)
def e2e_tenant(api: httpx.Client, admin_headers: dict):
    """Cria o tenant e2e_test no início da sessão e faz cleanup ao final."""
    # Cleanup anterior se existir
    api.patch(
        f"/admin/tenants/{E2E_TENANT_SLUG}/status",
        json={"status": "suspended"},
        headers=admin_headers,
    )

    resp = api.post(
        "/admin/tenants",
        json={
            "slug": E2E_TENANT_SLUG,
            "name": "E2E Test Tenant",
            "gestor_email": "e2e@intellicare.dev",
        },
        headers=admin_headers,
    )
    # 201 ou 409 (já existe)
    assert resp.status_code in (201, 409), f"Criar tenant falhou: {resp.text}"

    yield E2E_TENANT_SLUG

    # Teardown: reativar para não deixar estado sujo
    api.patch(
        f"/admin/tenants/{E2E_TENANT_SLUG}/status",
        json={"status": "active"},
        headers=admin_headers,
    )

