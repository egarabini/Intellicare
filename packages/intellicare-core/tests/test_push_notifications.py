"""Testes DEM-066 — Notificações Push PWA."""
import pytest
from uuid import uuid4
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Dependencias do projeto
from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from modules.notifications.router import router as notifications_router
from modules.notifications.service import NotificationService
from pywebpush import WebPushException

# Mock Context
TENANT_SLUG = "push_test_tenant"
TENANT_SCHEMA = f"tenant_{TENANT_SLUG}"
MOCK_UUID = "123e4567-e89b-12d3-a456-426614174000"

def _mock_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug=TENANT_SLUG,
        user_id=MOCK_UUID,
        roles=["CLINICO"],
        email="clinico@push.local",
    )

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(notifications_router, prefix="/api/v1/notifications")
    app.dependency_overrides[get_current_tenant] = _mock_ctx
    return app

@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
async def isolated_schema(app: FastAPI):
    # Setup the table in tests using sqlalchemy
    from intellicare_core.db.session import get_engine
    from sqlalchemy import text
    async with get_engine().begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TENANT_SCHEMA}"))
        await conn.execute(text(f"CREATE TABLE IF NOT EXISTS {TENANT_SCHEMA}.users (id UUID PRIMARY KEY, name TEXT);"))
        await conn.execute(text(f"INSERT INTO {TENANT_SCHEMA}.users (id, name) VALUES ('{MOCK_UUID}', 'Mock Clinico') ON CONFLICT DO NOTHING;"))
        await conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {TENANT_SCHEMA}.push_subscriptions (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      TEXT NOT NULL,
            endpoint     TEXT NOT NULL,
            p256dh       TEXT NOT NULL,
            auth         TEXT NOT NULL,
            user_agent   VARCHAR(255),
            created_at   TIMESTAMPTZ DEFAULT now(),
            last_used_at TIMESTAMPTZ,
            UNIQUE(user_id, endpoint)
        );
        """))
        await conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {TENANT_SCHEMA}.notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id TEXT NOT NULL,
            type TEXT,
            priority TEXT,
            title TEXT,
            body TEXT,
            data JSONB,
            read BOOLEAN DEFAULT FALSE,
            read_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
    yield
    async with get_engine().begin() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TENANT_SCHEMA} CASCADE"))


# ────────────────────────────────────────────────────────────────────────────
# Testes
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subscribe_saves_subscription(client: AsyncClient):
    resp = await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake1",
        "keys": {"p256dh": "p1", "auth": "a1"},
        "user_agent": "Mozilla"
    })
    assert resp.status_code == 201
    assert resp.json() == {"status": "subscribed"}

@pytest.mark.asyncio
async def test_duplicate_subscribe_is_idempotent(client: AsyncClient):
    await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake2",
        "keys": {"p256dh": "p2", "auth": "a2"}
    })
    resp = await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake2",
        "keys": {"p256dh": "p2_novo", "auth": "a2_novo"}
    })
    assert resp.status_code == 201

@pytest.mark.asyncio
async def test_unsubscribe_removes_subscription(client: AsyncClient):
    await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake3",
        "keys": {"p256dh": "p3", "auth": "a3"}
    })
    resp = await client.request("DELETE", "/api/v1/notifications/push/unsubscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake3"
    })
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_push_sent_on_careplanner_message(client: AsyncClient, monkeypatch):
    await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/target1",
        "keys": {"p256dh": "p_target", "auth": "a_target"}
    })
    
    push_call_mocked = False
    
    async def mock_send_push(*args, **kwargs):
        nonlocal push_call_mocked
        push_call_mocked = True
        return True
    
    monkeypatch.setattr("modules.notifications.push_sender.send_push", mock_send_push)
    
    # Criar notificacao no banco via POST -> Service -> send_push
    resp = await client.post("/api/v1/notifications/send", json={
        "user_id": MOCK_UUID,
        "type": "message",
        "title": "Mensagem CarePlanner",
        "body": "Nova msg."
    })
    assert resp.status_code == 201
    assert push_call_mocked

@pytest.mark.asyncio
async def test_expired_subscription_auto_removed(client: AsyncClient, monkeypatch):
    await client.post("/api/v1/notifications/push/subscribe", json={
        "endpoint": "https://fcm.googleapis.com/fcm/send/expired_ep",
        "keys": {"p256dh": "exp", "auth": "exp"}
    })
    
    class FakeResponse:
        status_code = 410

    async def mock_send_push_broken(*args, **kwargs):
        raise WebPushException("Gone", response=FakeResponse())
        
    monkeypatch.setattr("modules.notifications.push_sender.send_push", mock_send_push_broken)
    
    await client.post("/api/v1/notifications/send", json={
        "user_id": MOCK_UUID,
        "type": "message",
        "title": "Aviso",
        "body": "Teste 410"
    })
    
    # Conferir se removeu
    serv = NotificationService()
    subs = await serv.get_push_subscriptions(_mock_ctx(), MOCK_UUID)
    assert not any(s["endpoint"] == "https://fcm.googleapis.com/fcm/send/expired_ep" for s in subs)
