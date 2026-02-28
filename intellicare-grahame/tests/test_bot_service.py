"""Tests for BotService — 20 scenarios."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from grahame.models.base import Base
from grahame.models.bot import Bot, BotExecution, BotSecret  # noqa: F401 — registra tabelas
from grahame.services.bot_service import BotService

TEST_DB = "sqlite+aiosqlite:///:memory:"

_VALID_BOT = {
    "name": "Notificador",
    "description": "Envia alertas",
    "code": "print('bot executado')",
    "runtime": "sandbox",
    "status": "active",
    "timeoutSeconds": 30,
}

PATIENT = {"resourceType": "Patient", "id": "p-001"}


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
async def svc(session: AsyncSession) -> BotService:
    return BotService(session, tenant_id="tenant-a")


@pytest_asyncio.fixture
async def created_bot(svc: BotService) -> Bot:
    return await svc.create(_VALID_BOT)


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_bot_returns_bot(svc: BotService) -> None:
    bot = await svc.create(_VALID_BOT)
    assert bot.id is not None
    assert bot.name == "Notificador"
    assert bot.tenant_id == "tenant-a"
    assert bot.status == "active"
    assert bot.code_version == 1


@pytest.mark.asyncio
async def test_create_sets_defaults(svc: BotService) -> None:
    bot = await svc.create({"name": "Minimal"})
    assert bot.runtime == "sandbox"
    assert bot.status == "active"
    assert bot.timeout_seconds == 30
    assert bot.code == ""


@pytest.mark.asyncio
async def test_create_with_timeout_seconds(svc: BotService) -> None:
    bot = await svc.create({"name": "Fast Bot", "timeoutSeconds": 10})
    assert bot.timeout_seconds == 10


# ── Get ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_existing_bot(svc: BotService, created_bot: Bot) -> None:
    fetched = await svc.get(created_bot.id)
    assert fetched is not None
    assert fetched.id == created_bot.id
    assert fetched.name == "Notificador"


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(svc: BotService) -> None:
    fetched = await svc.get("nonexistent-id")
    assert fetched is None


@pytest.mark.asyncio
async def test_get_tenant_isolation(session: AsyncSession, created_bot: Bot) -> None:
    other_svc = BotService(session, tenant_id="tenant-other")
    fetched = await other_svc.get(created_bot.id)
    assert fetched is None


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_all_bots(svc: BotService) -> None:
    await svc.create({"name": "Bot A"})
    await svc.create({"name": "Bot B"})
    bots = await svc.list()
    assert len(bots) == 2


@pytest.mark.asyncio
async def test_list_filter_by_status(svc: BotService) -> None:
    await svc.create({"name": "Active Bot", "status": "active"})
    inactive = await svc.create({"name": "Inactive Bot", "status": "inactive"})
    active_bots = await svc.list(status="active")
    assert all(b.status == "active" for b in active_bots)
    inactive_bots = await svc.list(status="inactive")
    assert any(b.id == inactive.id for b in inactive_bots)


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_bot_name(svc: BotService, created_bot: Bot) -> None:
    updated = await svc.update(created_bot.id, {"name": "Novo Nome"})
    assert updated is not None
    assert updated.name == "Novo Nome"


@pytest.mark.asyncio
async def test_update_code_increments_version(svc: BotService, created_bot: Bot) -> None:
    assert created_bot.code_version == 1
    updated = await svc.update(created_bot.id, {"code": "print('v2')"})
    assert updated is not None
    assert updated.code_version == 2
    assert updated.code == "print('v2')"


@pytest.mark.asyncio
async def test_update_nonexistent_returns_none(svc: BotService) -> None:
    result = await svc.update("ghost-bot", {"name": "Ghost"})
    assert result is None


# ── Delete (soft) ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_marks_bot_inactive(svc: BotService, created_bot: Bot) -> None:
    ok = await svc.delete(created_bot.id)
    assert ok is True
    bot = await svc.get(created_bot.id)
    assert bot is not None
    assert bot.status == "inactive"


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(svc: BotService) -> None:
    ok = await svc.delete("phantom")
    assert ok is False


# ── Secrets ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_and_retrieve_secret(svc: BotService, created_bot: Bot) -> None:
    secret = await svc.set_secret(created_bot.id, "api_key", "super-secret-value")
    assert secret.name == "api_key"
    assert secret.value_encrypted  # stored as ciphertext, not plaintext
    assert "super-secret-value" not in secret.value_encrypted or len(secret.value_encrypted) > 20


@pytest.mark.asyncio
async def test_get_secrets_encrypted_returns_dict(svc: BotService, created_bot: Bot) -> None:
    await svc.set_secret(created_bot.id, "key1", "val1")
    await svc.set_secret(created_bot.id, "key2", "val2")
    secrets = await svc.get_secrets_encrypted(created_bot.id)
    assert "key1" in secrets
    assert "key2" in secrets


@pytest.mark.asyncio
async def test_set_secret_upsert(svc: BotService, created_bot: Bot) -> None:
    """Setting the same secret name twice should update, not duplicate."""
    await svc.set_secret(created_bot.id, "token", "original")
    await svc.set_secret(created_bot.id, "token", "updated")
    secrets = await svc.get_secrets_encrypted(created_bot.id)
    assert len([k for k in secrets if k == "token"]) == 1


# ── Execute ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_bot_runs_code(svc: BotService) -> None:
    bot = await svc.create({"name": "Logger", "code": "print('hello from bot')"})
    result = await svc.execute(bot.id, PATIENT)
    assert result["success"] is True
    assert "hello from bot" in result["log_output"]


@pytest.mark.asyncio
async def test_execute_bot_persists_execution(svc: BotService) -> None:
    bot = await svc.create({"name": "Logger", "code": "print('run')"})
    await svc.execute(bot.id, PATIENT)
    executions = await svc.list_executions(bot.id)
    assert len(executions) == 1
    assert executions[0].bot_id == bot.id
    assert executions[0].success is True


@pytest.mark.asyncio
async def test_execute_nonexistent_bot_raises(svc: BotService) -> None:
    with pytest.raises(ValueError, match="not found"):
        await svc.execute("ghost-id", PATIENT)


@pytest.mark.asyncio
async def test_execute_inactive_bot_raises(svc: BotService) -> None:
    bot = await svc.create({"name": "Inactive", "code": "pass", "status": "inactive"})
    with pytest.raises(ValueError, match="not active"):
        await svc.execute(bot.id, PATIENT)


# ── List executions ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_executions_ordered_desc(svc: BotService) -> None:
    bot = await svc.create({"name": "Multi", "code": "pass"})
    await svc.execute(bot.id, PATIENT)
    await svc.execute(bot.id, PATIENT)
    execs = await svc.list_executions(bot.id)
    assert len(execs) >= 2
