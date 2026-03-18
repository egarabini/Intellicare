from __future__ import annotations

import asyncio
from uuid import UUID

import pytest
from sqlalchemy import text
from fastapi import HTTPException

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.contracts import CareTemplateCreate
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.services import build_careplanner_service


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_phase_f_schema():
    await provision_tenant_schema("careplanner_test_f")
    async with get_engine().begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO public.tenants (slug, name, status)
                VALUES ('careplanner_test_f', 'careplanner_test_f', 'active')
                ON CONFLICT (slug) DO NOTHING
                """
            )
        )
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_f"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
async def clean_phase_f_tables():
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_f"'))
        await conn.execute(text("DELETE FROM care_templates"))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="careplanner_test_f",
        user_id="templates-test",
        roles=["GESTOR"],
        email="gestor@test.local",
    )


@pytest.fixture
def service():
    return build_careplanner_service()


@pytest.mark.asyncio
async def test_list_templates_vazio(service, tenant_ctx, clean_phase_f_tables):
    items = await service.list_templates(tenant_ctx)
    assert items == []


@pytest.mark.asyncio
async def test_create_template_sucesso(service, tenant_ctx, clean_phase_f_tables):
    payload = CareTemplateCreate(
        template_code="teste_01",
        channel="rocketchat",
        content="Ola mundo",
        variables=["nome"],
        active=True
    )
    res = await service.create_template_record(tenant_ctx, payload)
    
    assert res["template_code"] == "teste_01"
    assert res["content"] == "Ola mundo"
    assert res["variables"] == ["nome"]
    assert res["active"] is True
    assert "id" in res


@pytest.mark.asyncio
async def test_create_template_duplicate_409(service, tenant_ctx, clean_phase_f_tables):
    payload = CareTemplateCreate(
        template_code="teste_dup",
        channel="rocketchat",
        content="Conteudo original"
    )
    await service.create_template_record(tenant_ctx, payload)
    
    with pytest.raises(HTTPException) as exc:
        await service.create_template_record(tenant_ctx, payload)
    
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "template_already_exists"


@pytest.mark.asyncio
async def test_update_template(service, tenant_ctx, clean_phase_f_tables):
    payload = CareTemplateCreate(template_code="teste_upd", content="old")
    created = await service.create_template_record(tenant_ctx, payload)
    template_id = UUID(created["id"])
    
    res = await service.update_template_record(
        tenant_ctx,
        template_id=template_id,
        content="new content",
        variables=["x"],
        active=False
    )
    
    assert res["content"] == "new content"
    assert res["variables"] == ["x"]
    assert res["active"] is False


@pytest.mark.asyncio
async def test_toggle_template(service, tenant_ctx, clean_phase_f_tables):
    payload = CareTemplateCreate(template_code="teste_tog", content="tog", active=True)
    created = await service.create_template_record(tenant_ctx, payload)
    template_id = UUID(created["id"])
    
    res1 = await service.toggle_template(tenant_ctx, template_id)
    assert res1["active"] is False
    
    res2 = await service.toggle_template(tenant_ctx, template_id)
    assert res2["active"] is True
