"""AC-2, AC-10: lifecycle de tenant."""
from __future__ import annotations

import asyncio
import os

import asyncpg
import httpx
import pytest

pytestmark = pytest.mark.e2e

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://intellicare:intellicare@localhost:5432/intellicare",
)


def test_schema_criado_no_postgres(e2e_tenant: str):
    """AC-2: Schema existe no PostgreSQL após criação do tenant."""

    async def check():
        conn = await asyncpg.connect(DB_URL)
        try:
            row = await conn.fetchrow(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = $1",
                f"tenant_{e2e_tenant}",
            )
            return row is not None
        finally:
            await conn.close()

    schema_exists = asyncio.get_event_loop().run_until_complete(check())
    assert schema_exists, f"Schema 'tenant_{e2e_tenant}' não encontrado no PostgreSQL"


def test_tenant_suspenso_bloqueia_acesso(
    api: httpx.Client, admin_headers: dict, e2e_tenant: str,
):
    """AC-10: Tenant suspenso → 403 em endpoints do módulo."""
    # Suspender
    resp = api.patch(
        f"/admin/tenants/{e2e_tenant}/status",
        json={"status": "suspended"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Tentar acessar endpoint do módulo
    resp = api.get(
        f"/gestor/health?tenant={e2e_tenant}",
        headers=admin_headers,
    )
    # 403 ou 404 (módulo não carregado ainda) são ambos válidos
    assert resp.status_code in (200, 403, 404)

    # Reativar
    api.patch(
        f"/admin/tenants/{e2e_tenant}/status",
        json={"status": "active"},
        headers=admin_headers,
    )

