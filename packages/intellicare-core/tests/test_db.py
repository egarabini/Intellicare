from __future__ import annotations

import pytest
from sqlalchemy import text

from intellicare_core.contracts import TenantContext
from intellicare_core.db import TenantAwareSessionFactory, check_db_connection, tenant_session
from intellicare_core.db.migrations import provision_tenant_schema


@pytest.mark.asyncio
async def test_check_db_connection() -> None:
    assert await check_db_connection() is True


@pytest.mark.asyncio
async def test_tenant_aware_session_factory_sets_search_path() -> None:
    ctx = TenantContext.from_slug("dev", "user-1", ["CLINICO"])
    factory = TenantAwareSessionFactory()

    async with factory.session(ctx) as session:
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar_one()

    assert "tenant_dev" in search_path


@pytest.mark.asyncio
async def test_provision_tenant_schema_creates_knowledge_base() -> None:
    await provision_tenant_schema("sdktest")
    ctx = TenantContext.from_slug("sdktest", "user-1", ["CLINICO"])

    async with tenant_session(ctx) as session:
        result = await session.execute(text("SELECT to_regclass('knowledge_base')"))
        assert result.scalar_one() == "knowledge_base"
