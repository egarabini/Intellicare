"""
Top-level conftest — provides shared e2e fixtures.
"""
from __future__ import annotations

import os

import httpx
import pytest

API_URL = os.getenv("E2E_API_URL", "http://localhost:9000")
KC_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KC_REALM = "intellicare"
KC_CLIENT_ID = "intellicare-service"
KC_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")


def _get_token(username: str, password: str) -> str:
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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def api() -> httpx.Client:
    with httpx.Client(base_url=API_URL, timeout=15) as client:
        yield client


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    return _auth_headers(_get_token("platform-admin", "Admin@2025!"))


@pytest.fixture(scope="session")
def gestor_headers() -> dict[str, str]:
    return _auth_headers(_get_token("gestor-dev", "Gestor@2025!"))


@pytest.fixture(scope="session")
def clinico_headers() -> dict[str, str]:
    return _auth_headers(_get_token("clinico-dev", "Clinico@2025!"))
