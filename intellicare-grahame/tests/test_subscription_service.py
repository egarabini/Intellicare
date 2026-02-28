"""Tests for SubscriptionService — 18 scenarios."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from grahame.models.base import Base
from grahame.models.subscription import Subscription, SubscriptionAudit  # noqa: F401
from grahame.services.subscription_service import (
    MAX_ERROR_COUNT,
    MAX_SUBSCRIPTIONS_PER_TENANT,
    SubscriptionService,
)

TEST_DB = "sqlite+aiosqlite:///:memory:"

_VALID_DATA = {
    "criteria": "Observation?status=final",
    "channel": {"type": "rest-hook", "endpoint": "https://example.com/hook"},
}


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
async def svc(session):
    return SubscriptionService(session, tenant_id="tenant-test")


# ── create ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_subscription(svc):
    sub = await svc.create(_VALID_DATA)
    assert sub.id is not None
    assert sub.status == "requested"
    assert sub.criteria == "Observation?status=final"
    assert sub.channel_type == "rest-hook"
    assert sub.tenant_id == "tenant-test"


@pytest.mark.asyncio
async def test_create_with_status_active(svc):
    data = {**_VALID_DATA, "status": "active"}
    sub = await svc.create(data)
    assert sub.status == "active"


@pytest.mark.asyncio
async def test_create_with_reason(svc):
    data = {**_VALID_DATA, "reason": "Alert on high glucose"}
    sub = await svc.create(data)
    assert sub.reason == "Alert on high glucose"


@pytest.mark.asyncio
async def test_create_rate_limit(svc):
    # Fill quota
    for _ in range(MAX_SUBSCRIPTIONS_PER_TENANT):
        await svc.create({**_VALID_DATA, "status": "active"})
    with pytest.raises(ValueError, match="active subscriptions"):
        await svc.create({**_VALID_DATA, "status": "active"})


# ── get & list ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_existing(svc):
    created = await svc.create(_VALID_DATA)
    fetched = await svc.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(svc):
    result = await svc.get("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_list_returns_all(svc):
    await svc.create(_VALID_DATA)
    await svc.create(_VALID_DATA)
    subs = await svc.list()
    assert len(subs) == 2


@pytest.mark.asyncio
async def test_list_filter_by_status(svc):
    data_active = {**_VALID_DATA, "status": "active"}
    await svc.create(data_active)
    await svc.create(_VALID_DATA)  # "requested"
    active = await svc.list(status="active")
    assert len(active) == 1


# ── update ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_status(svc):
    sub = await svc.create(_VALID_DATA)
    updated = await svc.update(sub.id, {"status": "active"})
    assert updated is not None
    assert updated.status == "active"


@pytest.mark.asyncio
async def test_update_criteria(svc):
    sub = await svc.create(_VALID_DATA)
    updated = await svc.update(sub.id, {"criteria": "Patient?gender=female"})
    assert updated.criteria == "Patient?gender=female"


@pytest.mark.asyncio
async def test_update_nonexistent_returns_none(svc):
    result = await svc.update("ghost-id", {"status": "active"})
    assert result is None


# ── delete ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_sets_off(svc):
    sub = await svc.create(_VALID_DATA)
    ok = await svc.delete(sub.id)
    assert ok
    fetched = await svc.get(sub.id)
    assert fetched.status == "off"
    assert fetched.active is False


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(svc):
    ok = await svc.delete("ghost-id")
    assert not ok


# ── delivery tracking ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_success_resets_error_count(svc):
    data = {**_VALID_DATA, "status": "active"}
    sub = await svc.create(data)
    # Simulate prior failures
    sub.error_count = 3
    await svc.session.commit()
    await svc.record_delivery_result(sub.id, success=True)
    fetched = await svc.get(sub.id)
    assert fetched.error_count == 0


@pytest.mark.asyncio
async def test_record_failure_increments_error_count(svc):
    data = {**_VALID_DATA, "status": "active"}
    sub = await svc.create(data)
    await svc.record_delivery_result(sub.id, success=False, error="timeout")
    fetched = await svc.get(sub.id)
    assert fetched.error_count == 1


@pytest.mark.asyncio
async def test_error_threshold_deactivates_subscription(svc):
    data = {**_VALID_DATA, "status": "active"}
    sub = await svc.create(data)
    # Trigger MAX_ERROR_COUNT failures
    for _ in range(MAX_ERROR_COUNT):
        await svc.record_delivery_result(sub.id, success=False, error="net error")
    fetched = await svc.get(sub.id)
    assert fetched.status == "error"
    assert fetched.active is False


# ── fetch_active ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_active_filters_by_resource_type(svc):
    await svc.create({**_VALID_DATA, "status": "active"})  # Observation
    await svc.create({
        "criteria": "Patient?gender=female",
        "status": "active",
        "channel": {"type": "rest-hook", "endpoint": "https://x.com"},
    })
    results = await svc.fetch_active("tenant-test", "Observation")
    # Should only return the Observation subscription
    assert all("Observation" in r.criteria or "?" not in r.criteria for r in results)
