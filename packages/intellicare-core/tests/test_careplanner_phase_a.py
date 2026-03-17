from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from intellicare_core.contracts import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.contracts import (
    CareConversationUpsert,
    CareEventCreate,
    CareTaskCreate,
    EventType,
    TaskStatus,
)
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_schema():
    await provision_tenant_schema("careplanner_test")

    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="careplanner_test",
        user_id="clinico-careplanner-1",
        roles=["CLINICO"],
        email="clinico@test.local",
    )


@pytest.fixture
async def clean_tables():
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test"'))
        await conn.execute(text("DELETE FROM care_video_sessions"))
        await conn.execute(text("DELETE FROM care_templates"))
        await conn.execute(text("DELETE FROM care_events"))
        await conn.execute(text("DELETE FROM care_conversations"))
        await conn.execute(text("DELETE FROM care_tasks"))
        await conn.execute(text("SET search_path TO public"))


def test_task_status_transition_rules():
    TaskStatus.CREATED.ensure_transition(TaskStatus.DISPATCHED)
    TaskStatus.DISPATCHED.ensure_transition(TaskStatus.SENT)
    TaskStatus.SENT.ensure_transition(TaskStatus.REPLIED)

    with pytest.raises(ValueError):
        TaskStatus.CREATED.ensure_transition(TaskStatus.SENT)

    with pytest.raises(ValueError):
        TaskStatus.CLOSED.ensure_transition(TaskStatus.DISPATCHED)


@pytest.mark.asyncio
async def test_repository_event_idempotency(tenant_ctx: TenantContext, clean_tables):
    repo = CareplannerRepository()
    correlation_id = uuid4()

    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-001",
            task_type="CONTATO_INICIAL",
        ),
    )

    created_event, created = await repo.record_event_if_new(
        tenant_ctx,
        CareEventCreate(
            event_id="evt-care-001",
            correlation_id=correlation_id,
            event_type=EventType.MESSAGE_SENT,
            status=TaskStatus.SENT,
            payload={"rc_room_id": "ROOM-1"},
        ),
    )
    duplicated_event, duplicated = await repo.record_event_if_new(
        tenant_ctx,
        CareEventCreate(
            event_id="evt-care-001",
            correlation_id=correlation_id,
            event_type=EventType.MESSAGE_SENT,
            status=TaskStatus.SENT,
            payload={"rc_room_id": "ROOM-1"},
        ),
    )

    assert created is True
    assert duplicated is False
    assert created_event.id == duplicated_event.id

    events = await repo.list_events(tenant_ctx, correlation_id)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_repository_casts_channel_conversation_id_to_bigint(tenant_ctx: TenantContext, clean_tables):
    repo = CareplannerRepository()
    correlation_id = uuid4()

    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-002",
            task_type="FOLLOW_UP",
        ),
    )

    conversation = await repo.upsert_conversation(
        tenant_ctx,
        CareConversationUpsert(
            correlation_id=correlation_id,
            channel_conversation_id="85",
            rc_room_id="GENERAL_xyz",
        ),
    )

    assert conversation.channel_conversation_id == 85
    assert isinstance(conversation.channel_conversation_id, int)
