"""Tests for AccessPolicyService — 22 scenarios."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from grahame.models.base import Base
from grahame.models.access_policy import AccessPolicy, TenantMembership  # noqa: F401
from grahame.services.access_policy_service import AccessPolicyService

TEST_DB = "sqlite+aiosqlite:///:memory:"

_POLICY_DATA = {
    "name": "Enfermeiro - Setor A",
    "description": "Acesso básico para enfermeiros",
    "resourceRules": [
        {"resource_type": "Patient", "interaction": ["read", "search"]},
        {"resource_type": "Observation", "interaction": ["read", "search", "create"]},
    ],
}


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DB, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def svc(session: AsyncSession) -> AccessPolicyService:
    return AccessPolicyService(session, tenant_id="tenant-a")


@pytest_asyncio.fixture
async def created_policy(svc: AccessPolicyService) -> AccessPolicy:
    return await svc.create(_POLICY_DATA)


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_policy(svc: AccessPolicyService) -> None:
    policy = await svc.create(_POLICY_DATA)
    assert policy.id is not None
    assert policy.name == "Enfermeiro - Setor A"
    assert policy.tenant_id == "tenant-a"
    assert len(policy.resource_rules) == 2


@pytest.mark.asyncio
async def test_create_policy_minimal(svc: AccessPolicyService) -> None:
    policy = await svc.create({"name": "Admin Policy"})
    assert policy.name == "Admin Policy"
    assert policy.resource_rules == []
    assert policy.compartment_ref is None


@pytest.mark.asyncio
async def test_create_policy_with_compartment(svc: AccessPolicyService) -> None:
    data = {**_POLICY_DATA, "compartmentRef": "Organization/setor-a"}
    policy = await svc.create(data)
    assert policy.compartment_ref == "Organization/setor-a"


# ── Get ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_existing_policy(svc: AccessPolicyService, created_policy) -> None:
    fetched = await svc.get(created_policy.id)
    assert fetched is not None
    assert fetched.id == created_policy.id


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(svc: AccessPolicyService) -> None:
    assert await svc.get("ghost") is None


@pytest.mark.asyncio
async def test_get_tenant_isolation(session, created_policy) -> None:
    other_svc = AccessPolicyService(session, tenant_id="tenant-other")
    fetched = await other_svc.get(created_policy.id)
    assert fetched is None


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_policies(svc: AccessPolicyService) -> None:
    await svc.create({"name": "P1"})
    await svc.create({"name": "P2"})
    policies = await svc.list()
    assert len(policies) == 2


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_policy_name(svc, created_policy) -> None:
    updated = await svc.update(created_policy.id, {"name": "Novo Nome"})
    assert updated is not None
    assert updated.name == "Novo Nome"


@pytest.mark.asyncio
async def test_update_resource_rules(svc, created_policy) -> None:
    new_rules = [{"resource_type": "Patient", "interaction": ["read"]}]
    updated = await svc.update(created_policy.id, {"resourceRules": new_rules})
    assert len(updated.resource_rules) == 1


@pytest.mark.asyncio
async def test_update_nonexistent_returns_none(svc) -> None:
    assert await svc.update("ghost", {"name": "X"}) is None


# ── Delete ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_policy(svc, created_policy) -> None:
    ok = await svc.delete(created_policy.id)
    assert ok is True
    assert await svc.get(created_policy.id) is None


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(svc) -> None:
    assert await svc.delete("ghost") is False


# ── TenantMembership ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assign_policy_to_user(svc, created_policy) -> None:
    membership = await svc.assign_policy("user-123", created_policy.id)
    assert membership.user_id == "user-123"
    assert membership.access_policy_id == created_policy.id
    assert membership.is_admin is False


@pytest.mark.asyncio
async def test_assign_admin_membership(svc) -> None:
    membership = await svc.assign_policy("admin-user", None, is_admin=True)
    assert membership.is_admin is True


@pytest.mark.asyncio
async def test_assign_with_parameters(svc, created_policy) -> None:
    params = {"%profile": "Practitioner/dr-jose"}
    membership = await svc.assign_policy("user-456", created_policy.id, parameters=params)
    assert membership.parameters == params


@pytest.mark.asyncio
async def test_assign_policy_upsert(svc, created_policy) -> None:
    """Assigning same (user, policy) twice should not create duplicate."""
    await svc.assign_policy("user-999", created_policy.id)
    await svc.assign_policy("user-999", created_policy.id, parameters={"x": "y"})
    memberships = await svc.get_memberships("user-999")
    # Should be only one
    assert len(memberships) == 1


@pytest.mark.asyncio
async def test_get_memberships_for_user(svc, created_policy) -> None:
    policy2 = await svc.create({"name": "P2"})
    await svc.assign_policy("user-001", created_policy.id)
    await svc.assign_policy("user-001", policy2.id)
    memberships = await svc.get_memberships("user-001")
    assert len(memberships) == 2


@pytest.mark.asyncio
async def test_remove_membership(svc, created_policy) -> None:
    membership = await svc.assign_policy("user-111", created_policy.id)
    ok = await svc.remove_membership(membership.id)
    assert ok is True
    remaining = await svc.get_memberships("user-111")
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_membership(svc) -> None:
    assert await svc.remove_membership("ghost-id") is False


# ── PolicyBuilder integration callables ───────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_memberships_for_user(svc, created_policy) -> None:
    await svc.assign_policy("user-builder", created_policy.id)
    memberships = await svc.fetch_memberships_for_user("tenant-a", "user-builder")
    assert len(memberships) == 1
    assert memberships[0].user_id == "user-builder"


@pytest.mark.asyncio
async def test_fetch_policy_by_id_returns_pydantic(svc, created_policy) -> None:
    from intellicare_core.access.models import AccessPolicyRecord
    result = await svc.fetch_policy_by_id(created_policy.id)
    assert result is not None
    assert isinstance(result, AccessPolicyRecord)
    assert result.name == "Enfermeiro - Setor A"
    assert len(result.resource_rules) == 2


@pytest.mark.asyncio
async def test_fetch_policy_by_id_nonexistent_returns_none(svc) -> None:
    result = await svc.fetch_policy_by_id("ghost-policy-id")
    assert result is None
