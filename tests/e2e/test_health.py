"""AC-1: Todos os health checks retornam healthy em < 2s."""
from __future__ import annotations

import pytest
import httpx
from .conftest import API_URL, KC_URL

pytestmark = pytest.mark.e2e


def test_api_health(api: httpx.Client):
    resp = api.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_admin_module_health(api: httpx.Client, admin_headers: dict):
    resp = api.get("/admin/health", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["module"] == "admin"


def test_keycloak_health():
    resp = httpx.get(
        f"{KC_URL}/realms/intellicare/.well-known/openid-configuration",
        timeout=10,
    )
    assert resp.status_code == 200
    assert "token_endpoint" in resp.json()

