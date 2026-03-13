#!/usr/bin/env python3
"""
test_keycloak.py - Teste de integracao Keycloak <-> verify_token().
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "infra" / ".env"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file(ENV_PATH)

KC_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "intellicare-service")
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")
REALM = os.getenv("KEYCLOAK_REALM", "intellicare")


def get_token(username: str, password: str) -> str:
    response = httpx.post(
        f"{KC_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "openid",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def run_tests() -> None:
    sys.path.insert(0, str(ROOT))
    from intellicare_core.auth.jwt import verify_token

    test_matrix = [
        ("gestor-dev", "Gestor@2025!", "TENANT_GESTOR", "dev"),
        ("clinico-dev", "Clinico@2025!", "CLINICO", "dev"),
    ]

    for username, password, expected_role, expected_tenant in test_matrix:
        print(f"\nTestando user '{username}'...")
        token = get_token(username, password)
        ctx = await verify_token(token)

        assert ctx.tenant_id == expected_tenant, (
            f"FAIL tenant_id: esperado='{expected_tenant}' obtido='{ctx.tenant_id}'"
        )
        assert ctx.has_role(expected_role), (
            f"FAIL role: esperado='{expected_role}' roles={ctx.roles}"
        )
        assert ctx.schema == f"tenant_{expected_tenant}", (
            f"FAIL schema: esperado='tenant_{expected_tenant}' obtido='{ctx.schema}'"
        )

        print(f"  [PASS] tenant_id={ctx.tenant_id} roles={ctx.roles} schema={ctx.schema}")

    print("\nTodos os testes passaram.")


if __name__ == "__main__":
    asyncio.run(run_tests())
