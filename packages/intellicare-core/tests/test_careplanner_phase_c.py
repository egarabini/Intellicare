from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.db.session import get_engine
from modules.careplanner.api.routes import get_service, router as careplanner_router
from modules.careplanner.config import CareplannerSettings
from modules.careplanner.contracts import CareConversationUpsert, CareTaskCreate, TaskStatus
from modules.careplanner.integrations import notify_clinico_replied, trigger_cuidado_encounter
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository
from modules.careplanner.services import CareplannerService


class MockRocketChatAdapter:
    def __init__(self):
        self.posted_messages = []
        self.archived_rooms = []

    async def ensure_room(self, tenant_slug, patient_ref):
        return f"ROOM_ic_{tenant_slug}_{patient_ref}"

    async def post_message(self, rc_room_id, text):
        self.posted_messages.append({"room": rc_room_id, "text": text})
        return {"_id": "msg_001"}

    async def archive_room(self, rc_room_id):
        self.archived_rooms.append(rc_room_id)

    def verify_webhook_signature(self, payload, signature):
        return signature == "valid"


class MockKestraAdapter:
    async def resume_execution(self, execution_id, payload=None):
        return {"status": "RUNNING"}


class MockJitsiAdapter:
    def build_room_name(self, tenant_slug: str, correlation_id_str: str) -> str:
        return f"ic_{tenant_slug}_{correlation_id_str.replace('-', '')[:8]}"

    def generate_room_jwt(self, room_name, user_id, user_name, is_moderator=False, expires_in_minutes=None):
        return f"jwt-{room_name}-{user_id}"

    def get_room_url(self, room_name, jwt_token):
        return f"https://meet.intellicare.ia.br/{room_name}?jwt={jwt_token}"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_careplanner_phase_c_schema():
    await provision_tenant_schema("careplanner_test")
    async with get_engine().begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO public.tenants (slug, name, status)
                VALUES ('careplanner_test', 'careplanner_test', 'active')
                ON CONFLICT (slug) DO NOTHING
                """
            )
        )
        await conn.execute(text('SET search_path TO "tenant_careplanner_test"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
async def clean_phase_c_tables():
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_careplanner_test"'))
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
        user_id="clinico-careplanner-c",
        roles=["CLINICO", "TENANT_GESTOR"],
        email="clinico@test.local",
    )


def _mock_channel_adapters():
    whatsapp_mock = MagicMock()
    whatsapp_mock.send_message = AsyncMock(return_value={"key": {"id": "mock-wa"}})
    whatsapp_mock.close = AsyncMock()

    email_mock = MagicMock()
    email_mock.send_message = AsyncMock(return_value={"data": {}})
    email_mock.close = AsyncMock()

    sms_mock = MagicMock()
    sms_mock.send_message = AsyncMock(return_value={"status": "sent"})
    sms_mock.close = AsyncMock()
    return whatsapp_mock, email_mock, sms_mock


@pytest.fixture
def service() -> CareplannerService:
    settings = CareplannerSettings(
        jitsi_app_secret="secret-careplanner",
        rocketchat_webhook_token="secret-hmac",
    )
    whatsapp_mock, email_mock, sms_mock = _mock_channel_adapters()
    return CareplannerService(
        repo=CareplannerRepository(),
        rc=MockRocketChatAdapter(),
        jitsi=MockJitsiAdapter(),
        kestra=MockKestraAdapter(),
        whatsapp=whatsapp_mock,
        email=email_mock,
        sms=sms_mock,
        settings=settings,
    )


@pytest.fixture
def test_app() -> FastAPI:
    application = FastAPI()
    application.include_router(careplanner_router, prefix="/careplanner")
    return application


@pytest.mark.asyncio
async def test_notify_clinico_replied_calls_publish_notification():
    with patch("modules.notifications.service.NotificationService.send", new_callable=AsyncMock) as mock_send, \
         patch("modules.notifications.redis_pubsub.publish_broadcast", new_callable=AsyncMock) as mock_broadcast:
        ctx = TenantContext.from_slug("test_c", "user-1", roles=["CLINICO"])
        correlation_id = uuid4()
        await notify_clinico_replied(
            ctx,
            correlation_id=correlation_id,
            task_type="CONTATO_INICIAL",
            patient_ref="PAC-001",
            clinico_ref="dr.silva",
            content="SIM",
        )

        mock_send.assert_called_once()
        args = mock_send.call_args.args
        assert args[0].tenant_id == "test_c"
        assert args[1].user_id == "dr.silva"
        assert args[1].type == "message"
        assert args[1].priority == "high"
        assert args[1].data["event"] == "REPLIED"
        assert args[1].data["correlation_id"] == str(correlation_id)
        mock_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_notify_clinico_replied_swallows_errors():
    with patch("modules.notifications.service.NotificationService.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = RuntimeError("notification down")
        ctx = TenantContext.from_slug("test_c", "user-1", roles=["CLINICO"])
        await notify_clinico_replied(
            ctx,
            correlation_id=uuid4(),
            task_type="CONTATO_INICIAL",
            patient_ref="PAC-001",
            clinico_ref="dr.silva",
            content="SIM",
        )


@pytest.mark.asyncio
async def test_notify_clinico_replied_calls_broadcast_when_no_clinico():
    with patch("modules.notifications.redis_pubsub.publish_broadcast", new_callable=AsyncMock) as mock_pub:
        ctx = TenantContext.from_slug("test_c", "user-1", roles=["CLINICO"])
        await notify_clinico_replied(
            ctx,
            correlation_id=uuid4(),
            task_type="CONTATO_INICIAL",
            patient_ref="PAC-001",
            clinico_ref=None,
            content="SIM",
        )
        mock_pub.assert_called_once()
        assert mock_pub.call_args.args[0] == "test_c"


@pytest.mark.asyncio
async def test_trigger_cuidado_encounter_publishes_redis_event():
    mock_redis = AsyncMock()
    with patch("modules.notifications.redis_pubsub.get_redis", new_callable=AsyncMock, return_value=mock_redis):
        ctx = TenantContext.from_slug("test_c", "user-1", roles=["CLINICO"])
        correlation_id = uuid4()
        await trigger_cuidado_encounter(
            ctx,
            correlation_id=correlation_id,
            task_type="CONTATO_INICIAL",
            patient_ref="PAC-001",
        )
        mock_redis.publish.assert_called_once()
        channel, payload = mock_redis.publish.call_args.args
        assert channel == "careplanner:test_c:replied"
        data = json.loads(payload)
        assert data["event"] == "REPLIED"
        assert data["correlation_id"] == str(correlation_id)


@pytest.mark.asyncio
async def test_open_task_enqueues_dispatch(service: CareplannerService, tenant_ctx: TenantContext, clean_phase_c_tables):
    with patch("modules.careplanner.services.enqueue_dispatch", new_callable=AsyncMock) as mock_enqueue:
        result = await service.open_task(
            tenant_ctx,
            kestra_execution_id="exec-metric-001",
            patient_ref="PAC-METRIC",
            task_type="CONTATO_INICIAL",
            template_code="BOAS_VINDAS",
            template_variables={},
        )
    mock_enqueue.assert_called_once()
    assert result["status"] == "CREATED"


@pytest.mark.asyncio
async def test_process_inbound_invokes_notify_integration(
    service: CareplannerService,
    tenant_ctx: TenantContext,
    clean_phase_c_tables,
):
    repo = CareplannerRepository()
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            kestra_execution_id="exec-inbound-001",
            patient_ref="PAC-123",
            task_type="CONTATO_INICIAL",
            status=TaskStatus.SENT,
        ),
    )
    await repo.upsert_conversation(
        tenant_ctx,
        CareConversationUpsert(
            correlation_id=correlation_id,
            channel_conversation_id="85",
            rc_room_id="ROOM_ic_careplanner_test_PAC-123",
        ),
    )

    with patch("modules.careplanner.services.notify_clinico_replied", new_callable=AsyncMock) as mock_notify, \
         patch("modules.careplanner.services.trigger_cuidado_encounter", new_callable=AsyncMock) as mock_trigger:
        result = await service.process_inbound(
            tenant_ctx,
            event_id="evt-inbound-c-001",
            rc_room_id="ROOM_ic_careplanner_test_PAC-123",
            channel_conversation_id="85",
            content="SIM",
        )

    assert result["status"] == "REPLIED"
    mock_notify.assert_called_once()
    mock_trigger.assert_called_once()


@pytest.mark.asyncio
async def test_dashboard_stats_endpoint_returns_statuses(
    test_app: FastAPI,
    service: CareplannerService,
    tenant_ctx: TenantContext,
    clean_phase_c_tables,
):
    repo = CareplannerRepository()
    correlation_id = uuid4()
    await repo.create_task(
        tenant_ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-DASH",
            task_type="FOLLOW_UP",
            status=TaskStatus.REPLIED,
        ),
    )

    async def override_tenant():
        return tenant_ctx

    test_app.dependency_overrides[get_current_tenant] = override_tenant
    test_app.dependency_overrides[get_service] = lambda: service
    try:
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.get("/careplanner/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert set(data["by_status"].keys()) == {
            "CREATED", "DISPATCHED", "SENT", "REPLIED", "CLOSED", "FAILED", "EXPIRED"
        }
        assert isinstance(data["recent_tasks"], list)
        assert data["by_status"]["REPLIED"] >= 1
    finally:
        test_app.dependency_overrides.clear()
