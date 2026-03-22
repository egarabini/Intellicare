"""
DEM-050 — Testes de integração multi-canal CarePlanner.
Cobre dispatch WhatsApp, inbound REPLIED, falha para FAILED e não-regressão Rocket.Chat.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.adapters.whatsapp import WhatsAppAdapter
from modules.careplanner.config import CareplannerSettings
from modules.careplanner.contracts import Channel, TaskStatus
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository
from modules.careplanner.services import CareplannerService
from modules.careplanner.workers.dispatcher import _do_dispatch

sys.path.append(str(Path(__file__).parent))
from conftest_multicanal import mock_evolution_fail, mock_evolution_send  # noqa: F401


class MockRocketChatAdapter:
    def __init__(self) -> None:
        self.rooms: dict[str, str] = {}
        self.posted_messages: list[dict[str, str]] = []

    async def ensure_room(self, tenant_slug: str, patient_ref: str) -> str:
        room_id = f"ROOM_{tenant_slug}_{patient_ref}"
        self.rooms[patient_ref] = room_id
        return room_id

    async def post_message(self, rc_room_id: str, text: str) -> dict:
        self.posted_messages.append({"room": rc_room_id, "text": text})
        return {"_id": "rc-msg-001"}

    async def archive_room(self, rc_room_id: str) -> None:
        return None

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True


class MockKestraAdapter:
    def __init__(self) -> None:
        self.resumed: list[dict] = []

    async def resume_execution(self, execution_id: str, payload: dict | None = None) -> dict:
        self.resumed.append({"execution_id": execution_id, "payload": payload})
        return {"status": "RUNNING"}


class MockJitsiAdapter:
    def build_room_name(self, tenant_slug: str, correlation_id_str: str) -> str:
        return f"ic_{tenant_slug}_{correlation_id_str[:8]}"

    def generate_room_jwt(self, room_name, user_id, user_name, is_moderator=False, expires_in_minutes=None):
        return f"jwt-{room_name}-{user_id}"

    def get_room_url(self, room_name: str, jwt_token: str) -> str:
        return f"https://meet.example/{room_name}?jwt={jwt_token}"

    def is_expired(self, expires_at) -> bool:
        return False


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_multicanal_schema():
    slug = "careplanner_test_multi"
    await provision_tenant_schema(slug)

    async with get_engine().begin() as conn:
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
        await conn.execute(text(f'SET search_path TO "tenant_{slug}"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
async def clean_multicanal_tables():
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test_multi"'))
        await conn.execute(text("DELETE FROM care_video_sessions"))
        await conn.execute(text("DELETE FROM care_templates"))
        await conn.execute(text("DELETE FROM care_events"))
        await conn.execute(text("DELETE FROM care_conversations"))
        await conn.execute(text("DELETE FROM care_tasks"))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="careplanner_test_multi",
        user_id="gestor-multi",
        roles=["GESTOR"],
        email="gestor@multi.test",
    )


@pytest.fixture
def repo() -> CareplannerRepository:
    return CareplannerRepository()


@pytest.fixture
def service() -> CareplannerService:
    settings = CareplannerSettings(
        evolution_api_url="http://evolution.mock",
        evolution_api_key="mock-key",
        evolution_instance_name="intellicare",
        evolution_webhook_secret="test-secret",
    )
    return CareplannerService(
        repo=CareplannerRepository(),
        rc=MockRocketChatAdapter(),
        jitsi=MockJitsiAdapter(),
        kestra=MockKestraAdapter(),
        whatsapp=WhatsAppAdapter(settings),
        sms=SimpleNamespace(send_message=AsyncMock(return_value={"sid": "sms-001"})),
        email=SimpleNamespace(send_message=AsyncMock(return_value={"id": "email-001"})),
        settings=settings,
    )


@pytest.mark.asyncio
async def test_whatsapp_dispatch_calls_adapter_and_marks_sent(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_multicanal_tables,
    mock_evolution_send,
):
    opened = await service.open_task(
        tenant_ctx,
        kestra_execution_id="exec-wa-001",
        patient_ref="pac-001",
        task_type="CHECK_IN",
        template_code="check_in_wa",
        template_variables={},
        contact_phone="+5511999000001",
        channel=Channel.WHATSAPP,
    )

    correlation_id = UUID(opened["correlation_id"])
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    task = await repo.get_task(tenant_ctx, correlation_id)
    conversation = await repo.get_conversation(tenant_ctx, correlation_id)

    mock_evolution_send.assert_called_once()
    assert mock_evolution_send.call_args.args[0] == "+5511999000001"
    assert task is not None
    assert task.status == TaskStatus.SENT
    assert conversation is not None
    assert conversation.phone_e164 == "+5511999000001"


@pytest.mark.asyncio
async def test_whatsapp_inbound_transitions_to_replied(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_multicanal_tables,
    mock_evolution_send,
):
    opened = await service.open_task(
        tenant_ctx,
        kestra_execution_id="exec-wa-002",
        patient_ref="pac-002",
        task_type="CHECK_IN",
        template_code="check_in_wa",
        template_variables={},
        contact_phone="+5511999000002",
        channel=Channel.WHATSAPP,
    )

    correlation_id = UUID(opened["correlation_id"])
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    await service.handle_whatsapp_inbound(phone="5511999000002", text="Me sinto bem, obrigado!")
    task = await repo.get_task(tenant_ctx, correlation_id)

    assert task is not None
    assert task.status == TaskStatus.REPLIED
    assert service._kestra.resumed == [
        {
            "execution_id": "exec-wa-002",
            "payload": {
                "content": "Me sinto bem, obrigado!",
                "normalized_response": "OUTRO",
            },
        }
    ]


@pytest.mark.asyncio
async def test_whatsapp_dispatch_failure_marks_task_failed(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_multicanal_tables,
    mock_evolution_fail,
):
    opened = await service.open_task(
        tenant_ctx,
        kestra_execution_id="exec-wa-003",
        patient_ref="pac-003",
        task_type="CHECK_IN",
        template_code="check_in_wa",
        template_variables={},
        contact_phone="+5511999000003",
        channel=Channel.WHATSAPP,
    )

    correlation_id = UUID(opened["correlation_id"])
    mock_redis = SimpleNamespace(rpush=AsyncMock())
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service), patch(
        "modules.notifications.redis_pubsub.get_redis",
        new=AsyncMock(return_value=mock_redis),
    ):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    task = await repo.get_task(tenant_ctx, correlation_id)
    assert task is not None
    assert task.status == TaskStatus.FAILED
    assert mock_evolution_fail.await_count == 3
    mock_redis.rpush.assert_awaited()


@pytest.mark.asyncio
async def test_rocketchat_flow_unchanged(
    service: CareplannerService,
    repo: CareplannerRepository,
    tenant_ctx: TenantContext,
    clean_multicanal_tables,
):
    opened = await service.open_task(
        tenant_ctx,
        kestra_execution_id="exec-rc-001",
        patient_ref="pac-004",
        task_type="CHECK_IN",
        template_code="check_in",
        template_variables={},
        channel=Channel.ROCKETCHAT,
    )

    correlation_id = UUID(opened["correlation_id"])
    with patch("modules.careplanner.services.build_careplanner_service", return_value=service):
        await _do_dispatch({"correlation_id": str(correlation_id), "tenant_slug": tenant_ctx.tenant_id, "attempts": 0})

    task = await repo.get_task(tenant_ctx, correlation_id)

    assert task is not None
    assert task.status == TaskStatus.DISPATCHED
    assert len(service._rc.posted_messages) == 1
