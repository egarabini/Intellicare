from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import text

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.adapters.jitsi import JitsiAdapter
from modules.careplanner.adapters.rocketchat import RocketChatAdapter
from modules.careplanner.api.routes import get_service, router as careplanner_router
from modules.careplanner.config import CareplannerSettings
from modules.careplanner.contracts import (
    CareConversationUpsert,
    CareEventCreate,
    CareTaskCreate,
    EventType,
    TaskStatus,
    cast_channel_conversation_id,
)
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository
from modules.careplanner.services import CareplannerService
from modules.careplanner.workers.dispatcher import _do_dispatch


class MockRocketChatAdapter:
    def __init__(self):
        self.posted_messages = []
        self.archived_rooms = []
        self.rooms = {}

    async def login_bot(self):
        return None

    async def ensure_room(self, tenant_slug, patient_ref):
        name = f"ic_{tenant_slug}_{patient_ref}"
        self.rooms[name] = "ROOM_" + name
        return "ROOM_" + name

    async def post_message(self, rc_room_id, text):
        self.posted_messages.append({"room": rc_room_id, "text": text})
        return {"_id": "msg_001"}

    async def archive_room(self, rc_room_id):
        self.archived_rooms.append(rc_room_id)

    def verify_webhook_signature(self, payload, signature):
        return signature == "valid"


class MockKestraAdapter:
    def __init__(self):
        self.resumed = []

    async def resume_execution(self, execution_id, payload=None):
        self.resumed.append({"execution_id": execution_id, "payload": payload})
        return {"status": "RUNNING"}


class MockJitsiAdapter:
    def build_room_name(self, tenant_slug: str, correlation_id_str: str) -> str:
        return f"ic_{tenant_slug}_{correlation_id_str.replace('-', '')[:8]}"

    def generate_room_jwt(self, room_name, user_id, user_name, is_moderator=False, expires_in_minutes=None):
        role = "moderator" if is_moderator else "participant"
        return f"jwt-{room_name}-{user_id}-{role}"

    def get_room_url(self, room_name, jwt_token):
        return f"https://meet.intellicare.ia.br/{room_name}?jwt={jwt_token}"


@pytest.fixture
def test_app() -> FastAPI:
    application = FastAPI()
    application.include_router(careplanner_router, prefix="/careplanner")
    return application


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_phase_b_schemas():
    for slug in ["careplanner_test", "careplanner_test_b"]:
        await provision_tenant_schema(slug)

    async with get_engine().begin() as conn:
        for slug in ["careplanner_test", "careplanner_test_b"]:
            schema = f"tenant_{slug}"
            await conn.execute(
                text(
                    """
                    INSERT INTO public.tenants (slug, name, status)
                    VALUES (:slug, :name, 'active')
                    ON CONFLICT (slug) DO NOTHING
                    """
                ),
                {"slug": slug, "name": slug},
            )
            await conn.execute(text(f'SET search_path TO "{schema}"'))
            for sql in CAREPLANNER_MIGRATIONS:
                await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
async def clean_phase_b_tables():
    async with get_engine().begin() as conn:
        for slug in ["careplanner_test", "careplanner_test_b"]:
            schema = f"tenant_{slug}"
            await conn.execute(text(f'SET search_path TO "{schema}"'))
            await conn.execute(text("DELETE FROM care_video_sessions"))
            await conn.execute(text("DELETE FROM care_templates"))
            await conn.execute(text("DELETE FROM care_events"))
            await conn.execute(text("DELETE FROM care_conversations"))
            await conn.execute(text("DELETE FROM care_tasks"))
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
def tenant_ctx_b() -> TenantContext:
    return TenantContext.from_slug(
        slug="careplanner_test_b",
        user_id="clinico-careplanner-2",
        roles=["CLINICO"],
        email="clinico_b@test.local",
    )


@pytest.fixture
def repo() -> CareplannerRepository:
    return CareplannerRepository()


@pytest.fixture
def service() -> CareplannerService:
    settings = CareplannerSettings(
        jitsi_app_secret="secret-careplanner",
        rocketchat_webhook_token="secret-hmac",
    )
    return CareplannerService(
        repo=CareplannerRepository(),
        rc=MockRocketChatAdapter(),
        jitsi=MockJitsiAdapter(),
        kestra=MockKestraAdapter(),
        settings=settings,
    )


def _signature_for(body: dict, secret: str = "secret-hmac") -> str:
    payload = json.dumps(body).encode()
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_task_status_transition_rules_phase_b():
    TaskStatus.CREATED.ensure_transition(TaskStatus.DISPATCHED)
    TaskStatus.DISPATCHED.ensure_transition(TaskStatus.SENT)
    TaskStatus.SENT.ensure_transition(TaskStatus.REPLIED)

    with pytest.raises(ValueError):
        TaskStatus.CREATED.ensure_transition(TaskStatus.SENT)

    with pytest.raises(ValueError):
        TaskStatus.CLOSED.ensure_transition(TaskStatus.DISPATCHED)


@pytest.mark.asyncio
async def test_repository_event_idempotency_phase_b(repo: CareplannerRepository, tenant_ctx: TenantContext, clean_phase_b_tables):
    correlation_id = UUID("00000000-0000-0000-0000-000000000101")
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-001",
            task_type="CONTATO_INICIAL",
        ),
    )
    first, created_first = await repo.record_event_if_new(
        tenant_ctx,
        CareEventCreate(
            event_id="evt-dup-001",
            correlation_id=correlation_id,
            event_type=EventType.MESSAGE_SENT,
            status=TaskStatus.SENT,
            payload={},
        ),
    )
    second, created_second = await repo.record_event_if_new(
        tenant_ctx,
        CareEventCreate(
            event_id="evt-dup-001",
            correlation_id=correlation_id,
            event_type=EventType.MESSAGE_SENT,
            status=TaskStatus.SENT,
            payload={},
        ),
    )

    assert created_first is True
    assert created_second is False
    assert first.id == second.id


def test_cast_channel_conversation_id_phase_b():
    assert cast_channel_conversation_id("85") == 85
    with pytest.raises(ValueError):
        cast_channel_conversation_id("abc")


def test_rocketchat_hmac_verification():
    adapter = RocketChatAdapter(CareplannerSettings(rocketchat_webhook_token="secret-hmac"))
    payload = b'{"event":"ok"}'
    valid = "sha256=" + hmac.new(b"secret-hmac", payload, hashlib.sha256).hexdigest()

    assert adapter.verify_webhook_signature(payload, valid) is True
    assert adapter.verify_webhook_signature(payload, "sha256=invalid") is False


def test_jitsi_jwt_generation():
    settings = CareplannerSettings(
        jitsi_app_id="intellicare",
        jitsi_base_url="https://meet.intellicare.ia.br",
        jitsi_app_secret="jwt-secret",
        jitsi_default_room_duration=120,
    )
    adapter = JitsiAdapter(settings)
    room_name = adapter.build_room_name("alfa", "550e8400-e29b-41d4-a716-446655440000")
    token = adapter.generate_room_jwt(room_name, "dr.silva", "Dr Silva", is_moderator=True)
    payload = jwt.decode(token, "jwt-secret", algorithms=["HS256"], audience="jitsi")

    assert payload["iss"] == "intellicare"
    assert payload["sub"] == "https://meet.intellicare.ia.br"
    assert payload["moderator"] is True
    assert payload["context"]["user"]["id"] == "dr.silva"
    assert payload["room"] == "ic_alfa_550e8400"
    assert payload["exp"] > payload["iat"]
    assert payload["exp"] - payload["iat"] <= 120 * 60


@pytest.mark.asyncio
async def test_full_flow_open_dispatch_sent_reply(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_phase_b_tables,
):
    with patch("modules.careplanner.services.enqueue_dispatch", new_callable=AsyncMock) as mock_enqueue:
        opened = await service.open_task(
            tenant_ctx,
            kestra_execution_id="exec-001",
            patient_ref="PAC-123",
            task_type="CONTATO_INICIAL",
            template_code="BOAS_VINDAS",
            template_variables={"nome": "Maria"},
            contact_phone="+5531999999999",
        )
        mock_enqueue.assert_called_once()

    correlation_id = UUID(opened["correlation_id"])
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})
    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.DISPATCHED
    assert opened["status"] == TaskStatus.CREATED.value

    sent = await service.process_message_sent(
        tenant_ctx,
        event_id="evt-msg-sent-001",
        correlation_id=correlation_id,
        rc_room_id="ROOM_ic_careplanner_test_PAC-123",
        channel_conversation_id="85",
    )
    replied = await service.process_inbound(
        tenant_ctx,
        event_id="evt-inbound-001",
        rc_room_id="ROOM_ic_careplanner_test_PAC-123",
        channel_conversation_id="85",
        content="SIM",
        occurred_at="2026-03-17T10:00:00Z",
    )
    task = await repo.get_task(tenant_ctx, correlation_id)

    assert sent["status"] == "SENT"
    assert replied["status"] == "REPLIED"
    assert task is not None
    assert task.status == TaskStatus.REPLIED
    assert service._kestra.resumed == [{"execution_id": "exec-001", "payload": {"content": "SIM"}}]


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    tenant_ctx_b: TenantContext,
    clean_phase_b_tables,
):
    with patch("modules.careplanner.services.enqueue_dispatch", new_callable=AsyncMock):
        opened = await service.open_task(
            tenant_ctx,
            kestra_execution_id="exec-002",
            patient_ref="PAC-A",
            task_type="FOLLOW_UP",
            template_code="FOLLOWUP",
            template_variables={},
        )
    correlation_id = UUID(opened["correlation_id"])

    assert await repo.get_task(tenant_ctx, correlation_id) is not None
    assert await repo.get_task(tenant_ctx_b, correlation_id) is None


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_403(clean_phase_b_tables):
    mock_service = CareplannerService(
        repo=CareplannerRepository(),
        rc=MockRocketChatAdapter(),
        jitsi=MockJitsiAdapter(),
        kestra=MockKestraAdapter(),
        settings=CareplannerSettings(rocketchat_webhook_token="secret-hmac", jitsi_app_secret="secret"),
    )

    async def override_tenant():
        return TenantContext.from_slug("careplanner_test", "user-test", roles=["CLINICO"])

    application = FastAPI()
    application.include_router(careplanner_router, prefix="/careplanner")
    application.dependency_overrides[get_current_tenant] = override_tenant
    application.dependency_overrides[get_service] = lambda: mock_service
    try:
        payload = {
            "event_id": "evt-msg-sent-403",
            "correlation_id": "00000000-0000-0000-0000-000000000111",
            "event_type": "MESSAGE_SENT",
            "refs": {"rc_room_id": "ROOM_X", "channel_conversation_id": "85"},
        }
        async with AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as ac:
            response = await ac.post(
                "/careplanner/events/message-sent",
                json=payload,
                headers={"X-Rocketchat-Signature": "invalid"},
            )
        assert response.status_code == 403
    finally:
        application.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_orphan_inbound_records_event(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_phase_b_tables,
):
    result = await service.process_inbound(
        tenant_ctx,
        event_id="evt-orphan-001",
        rc_room_id="ROOM_UNKNOWN",
        channel_conversation_id="999",
        content="Oi",
    )

    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test"'))
        row = (
            await conn.execute(
                text("SELECT event_type FROM care_events WHERE event_id = 'evt-orphan-001'")
            )
        ).scalar_one()
        await conn.execute(text("SET search_path TO public"))

    assert result == {"ok": True, "orphan": True}
    assert row == "ORPHAN_INBOUND"


@pytest.mark.asyncio
async def test_close_task_archives_room(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_phase_b_tables,
):
    with patch("modules.careplanner.services.enqueue_dispatch", new_callable=AsyncMock) as mock_enqueue:
        opened = await service.open_task(
            tenant_ctx,
            kestra_execution_id="exec-003",
            patient_ref="PAC-CLOSE",
            task_type="FOLLOW_UP",
            template_code="FOLLOWUP",
            template_variables={},
        )
        mock_enqueue.assert_called_once()
    correlation_id = UUID(opened["correlation_id"])
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})
    await service.process_message_sent(
        tenant_ctx,
        event_id="evt-msg-sent-002",
        correlation_id=correlation_id,
        rc_room_id="ROOM_ic_careplanner_test_PAC-CLOSE",
        channel_conversation_id="88",
    )

    result = await service.close_task(tenant_ctx, correlation_id)
    task = await repo.get_task(tenant_ctx, correlation_id)

    assert result["status"] == "CLOSED"
    assert task is not None
    assert task.status == TaskStatus.CLOSED
    assert service._rc.archived_rooms == ["ROOM_ic_careplanner_test_PAC-CLOSE"]
