"""Testes DEM-054 — CarePlanner × Agendamento (link bidirecional)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
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
from modules.careplanner.contracts import CareTaskCreate, TaskStatus
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.careplanner.repository import CareplannerRepository
from modules.careplanner.services import CareplannerService

TENANT_SLUG = "careplanner_test_k"


class _MockRC:
    async def login_bot(self): pass
    async def ensure_room(self, *a): return "ROOM_K"
    async def post_message(self, *a): return {"_id": "msg_k"}
    async def archive_room(self, *a): pass
    def verify_webhook_signature(self, *a): return True


class _MockKestra:
    async def resume_execution(self, *a, **kw): return {"status": "RUNNING"}


class _MockJitsi:
    def build_room_name(self, *a): return "room_k"
    def generate_room_jwt(self, *a, **kw): return "jwt_k"
    def get_room_url(self, *a): return "https://meet.test/room_k"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_schema():
    await provision_tenant_schema(TENANT_SLUG)
    async with get_engine().begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO public.tenants (slug, name, status) "
                "VALUES (:slug, :name, 'active') "
                "ON CONFLICT (slug) DO NOTHING"
            ),
            {"slug": TENANT_SLUG, "name": TENANT_SLUG},
        )
        schema = f"tenant_{TENANT_SLUG}"
        await conn.execute(text(f'SET search_path TO "{schema}"'))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture(autouse=True)
async def clean_tables():
    yield
    async with get_engine().begin() as conn:
        schema = f"tenant_{TENANT_SLUG}"
        await conn.execute(text(f'SET search_path TO "{schema}"'))
        await conn.execute(text("DELETE FROM care_video_sessions"))
        await conn.execute(text("DELETE FROM care_templates"))
        await conn.execute(text("DELETE FROM care_events"))
        await conn.execute(text("DELETE FROM care_conversations"))
        await conn.execute(text("DELETE FROM care_tasks"))
        await conn.execute(text("SET search_path TO public"))


@pytest.fixture
def ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug=TENANT_SLUG,
        user_id="gestor-k-1",
        roles=["GESTOR"],
        email="gestor_k@test.local",
    )


@pytest.fixture
def repo() -> CareplannerRepository:
    return CareplannerRepository()


@pytest.fixture
def service() -> CareplannerService:
    wa = MagicMock(); wa.send_message = AsyncMock(return_value={"key": {"id": "m"}}); wa.close = AsyncMock()
    em = MagicMock(); em.send_message = AsyncMock(return_value={"data": {}}); em.close = AsyncMock()
    sm = MagicMock(); sm.send_message = AsyncMock(return_value={"status": "sent"}); sm.close = AsyncMock()
    return CareplannerService(
        repo=CareplannerRepository(),
        rc=_MockRC(),
        jitsi=_MockJitsi(),
        kestra=_MockKestra(),
        whatsapp=wa,
        email=em,
        sms=sm,
        settings=CareplannerSettings(
            jitsi_app_secret="secret-k",
            rocketchat_webhook_token="secret-k",
        ),
    )


# ────────────────────────────────────────────────────────────────────────────
# Test 1: link_task_to_appointment persiste corretamente
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_link_appointment_to_task(repo: CareplannerRepository, ctx: TenantContext):
    """open_task com appointment_id persiste o vínculo."""
    correlation_id = uuid4()
    appointment_id = uuid4()

    await repo.create_task(
        ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-K-001",
            task_type="CHECK_IN",
        ),
    )

    await repo.link_task_to_appointment(ctx, correlation_id, appointment_id)

    task = await repo.get_task(ctx, correlation_id)
    assert task is not None
    assert task.appointment_id == appointment_id


# ────────────────────────────────────────────────────────────────────────────
# Test 2: get_task_by_appointment retorna a task vinculada
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_task_by_appointment(repo: CareplannerRepository, ctx: TenantContext):
    """get_task_by_appointment retorna a task ativa vinculada."""
    correlation_id = uuid4()
    appointment_id = uuid4()

    await repo.create_task(
        ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-K-002",
            task_type="ADESAO",
        ),
    )
    await repo.link_task_to_appointment(ctx, correlation_id, appointment_id)

    found = await repo.get_task_by_appointment(ctx, appointment_id)
    assert found is not None
    assert found.correlation_id == correlation_id
    assert found.appointment_id == appointment_id


# ────────────────────────────────────────────────────────────────────────────
# Test 3: get_task_by_appointment retorna None quando inexistente
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_task_by_appointment_not_found(repo: CareplannerRepository, ctx: TenantContext):
    """get_task_by_appointment retorna None para agendamento sem jornada."""
    result = await repo.get_task_by_appointment(ctx, uuid4())
    assert result is None


# ────────────────────────────────────────────────────────────────────────────
# Test 4: endpoint GET /appointments/{id}/journey via HTTP
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_endpoint_journey_by_appointment(
    repo: CareplannerRepository, ctx: TenantContext, service: CareplannerService
):
    """GET /careplanner/appointments/{id}/journey retorna 200."""
    correlation_id = uuid4()
    appointment_id = uuid4()

    await repo.create_task(
        ctx,
        CareTaskCreate(
            correlation_id=correlation_id,
            patient_ref="PAC-K-003",
            task_type="MONITORAMENTO",
        ),
    )
    await repo.link_task_to_appointment(ctx, correlation_id, appointment_id)

    app = FastAPI()
    app.include_router(careplanner_router, prefix="/careplanner")
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_service] = lambda: service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(f"/careplanner/appointments/{appointment_id}/journey")
        assert resp.status_code == 200
        data = resp.json()
        assert data["correlation_id"] == str(correlation_id)
        assert data["appointment_id"] == str(appointment_id)


# ────────────────────────────────────────────────────────────────────────────
# Test 5: endpoint retorna 404 quando não há jornada
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_endpoint_journey_by_appointment_not_found(
    ctx: TenantContext, service: CareplannerService
):
    """GET /careplanner/appointments/{id}/journey retorna 404."""
    app = FastAPI()
    app.include_router(careplanner_router, prefix="/careplanner")
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_service] = lambda: service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(f"/careplanner/appointments/{uuid4()}/journey")
        assert resp.status_code == 404
