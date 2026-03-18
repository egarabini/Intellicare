from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.adapters.rocketchat import RocketChatAdapter
from modules.careplanner.config import CareplannerSettings
from modules.careplanner.contracts import CareTaskCreate, TaskStatus
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository
from modules.careplanner.security import mask_content, mask_phone
from modules.careplanner.workers.dispatcher import DEAD_KEY, QUEUE_KEY, _do_dispatch, enqueue_dispatch
from modules.careplanner.workers.expiry_worker import _expire_for_tenant


class FakeRedis:
    def __init__(self):
        self.items: list[tuple[str, str]] = []

    async def rpush(self, key: str, value: str):
        self.items.append((key, value))
        return len(self.items)


class FlakyRocketChat:
    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.post_calls = 0

    async def ensure_room(self, tenant_slug: str, patient_ref: str) -> str:
        return f"ROOM_ic_{tenant_slug}_{patient_ref}"

    async def post_message(self, rc_room_id: str, text: str):
        self.post_calls += 1
        if self.post_calls <= self.fail_times:
            raise RuntimeError("dispatch failure")
        return {"_id": "msg_001"}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_phase_d_schema():
    await provision_tenant_schema("careplanner_test_d")
    async with get_engine().begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO public.tenants (slug, name, status)
                VALUES ('careplanner_test_d', 'careplanner_test_d', 'active')
                ON CONFLICT (slug) DO NOTHING
                """
            )
        )
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_d"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
async def clean_phase_d_tables():
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_d"'))
        await conn.execute(text("DELETE FROM care_video_sessions"))
        await conn.execute(text("DELETE FROM care_templates"))
        await conn.execute(text("DELETE FROM care_events"))
        await conn.execute(text("DELETE FROM care_conversations"))
        await conn.execute(text("DELETE FROM care_tasks"))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="careplanner_test_d",
        user_id="dispatcher-worker-test",
        roles=["CLINICO"],
        email="clinico@test.local",
    )


@pytest.fixture
def repo() -> CareplannerRepository:
    return CareplannerRepository()


@pytest.mark.asyncio
async def test_enqueue_dispatch_pushes_json():
    fake_redis = FakeRedis()
    with patch("modules.notifications.redis_pubsub.get_redis", new_callable=AsyncMock, return_value=fake_redis):
        await enqueue_dispatch("corr-001", "tenant-a")

    assert len(fake_redis.items) == 1
    key, raw = fake_redis.items[0]
    assert key == QUEUE_KEY
    payload = json.loads(raw)
    assert payload["correlation_id"] == "corr-001"
    assert payload["tenant_slug"] == "tenant-a"
    assert payload["attempts"] == 0


@pytest.mark.asyncio
async def test_do_dispatch_retries_and_succeeds(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_d_tables):
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-D-001",
            task_type="CONTATO_INICIAL",
            metadata={
                "template_code": "BOAS_VINDAS",
                "template_variables": {},
                "contact_phone": "+5531999999999",
                "contact_role": "PACIENTE",
            },
        ),
    )
    flaky = FlakyRocketChat(fail_times=2)
    with patch("modules.careplanner.services.build_careplanner_service", return_value=SimpleNamespace(_rc=flaky)):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.DISPATCHED
    assert flaky.post_calls == 3


@pytest.mark.asyncio
async def test_do_dispatch_moves_to_dead_letter_and_failed(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_d_tables):
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-D-002",
            task_type="CONTATO_INICIAL",
            metadata={
                "template_code": "BOAS_VINDAS",
                "template_variables": {},
                "contact_role": "PACIENTE",
            },
        ),
    )
    fake_redis = FakeRedis()
    flaky = FlakyRocketChat(fail_times=3)
    with patch("modules.notifications.redis_pubsub.get_redis", new_callable=AsyncMock, return_value=fake_redis), \
         patch("modules.careplanner.services.build_careplanner_service", return_value=SimpleNamespace(_rc=flaky)):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.FAILED
    assert any(key == DEAD_KEY for key, _ in fake_redis.items)


def test_mask_phone():
    assert mask_phone("+5531999999999") == "+55319****9999"


def test_mask_content():
    assert mask_content("mensagem longa que excede vinte chars") == "mensagem longa que e[…]"


def test_verify_webhook_signature_without_prefix():
    adapter = RocketChatAdapter(CareplannerSettings(rocketchat_webhook_token="secret-hmac"))
    payload = b'{"event":"ok"}'
    signature = __import__("hmac").new(b"secret-hmac", payload, __import__("hashlib").sha256).hexdigest()
    assert adapter.verify_webhook_signature(payload, signature) is True


def test_verify_webhook_signature_invalid_length():
    adapter = RocketChatAdapter(CareplannerSettings(rocketchat_webhook_token="secret-hmac"))
    assert adapter.verify_webhook_signature(b"{}", "a" * 63) is False


@pytest.mark.asyncio
async def test_expire_dispatched_task(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_d_tables):
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-D-003",
            task_type="CONTATO_INICIAL",
            status=TaskStatus.DISPATCHED,
        ),
    )
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_d"'))
        await conn.execute(
            text("UPDATE care_tasks SET updated_at = NOW() - INTERVAL '25 hours' WHERE correlation_id = :correlation_id"),
            {"correlation_id": str(correlation_id)},
        )
        await conn.execute(text("SET search_path TO public"))

    await _expire_for_tenant(tenant_ctx, repo)
    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.EXPIRED


@pytest.mark.asyncio
async def test_expire_sent_task(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_d_tables):
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-D-004",
            task_type="CONTATO_INICIAL",
            status=TaskStatus.SENT,
        ),
    )
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_d"'))
        await conn.execute(
            text("UPDATE care_tasks SET updated_at = NOW() - INTERVAL '73 hours' WHERE correlation_id = :correlation_id"),
            {"correlation_id": str(correlation_id)},
        )
        await conn.execute(text("SET search_path TO public"))

    await _expire_for_tenant(tenant_ctx, repo)
    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.EXPIRED


@pytest.mark.asyncio
async def test_replied_task_does_not_expire(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_d_tables):
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-D-005",
            task_type="CONTATO_INICIAL",
            status=TaskStatus.REPLIED,
        ),
    )
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_d"'))
        await conn.execute(
            text("UPDATE care_tasks SET updated_at = NOW() - INTERVAL '100 hours' WHERE correlation_id = :correlation_id"),
            {"correlation_id": str(correlation_id)},
        )
        await conn.execute(text("SET search_path TO public"))

    await _expire_for_tenant(tenant_ctx, repo)
    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.REPLIED
