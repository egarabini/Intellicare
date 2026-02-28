"""Tests for BotExecutor — orchestration end-to-end."""

import pytest
import pytest_asyncio

from intellicare_core.bots.executor import BotExecutor
from intellicare_core.bots.models import BotExecutionResult, BotRecord, EventMetadata


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_bot(code: str, *, timeout: int = 30, status: str = "active") -> BotRecord:
    return BotRecord(
        id="bot-001",
        tenant_id="tenant-test",
        name="Test Bot",
        code=code,
        status=status,
        timeout_seconds=timeout,
    )


PATIENT_RESOURCE = {
    "resourceType": "Patient",
    "id": "p-001",
    "name": [{"family": "Silva", "given": ["Ana"]}],
}


# ── Basic execution ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_simple_code_succeeds() -> None:
    executor = BotExecutor()
    bot = _make_bot("print('bot ran')")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is True
    assert "bot ran" in result.log_output


@pytest.mark.asyncio
async def test_execute_returns_bot_execution_result() -> None:
    executor = BotExecutor()
    bot = _make_bot("pass")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert isinstance(result, BotExecutionResult)


@pytest.mark.asyncio
async def test_execute_result_fields_populated() -> None:
    executor = BotExecutor()
    bot = _make_bot("pass")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.bot_id == "bot-001"
    assert result.tenant_id == "tenant-test"
    assert result.input_resource_type == "Patient"
    assert result.input_resource_id == "p-001"
    assert result.duration_ms >= 0.0
    assert result.id  # UUID assigned


# ── Input resource access ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bot_can_read_input_resource() -> None:
    code = "print(input['resourceType'])\nprint(input['id'])"
    executor = BotExecutor()
    bot = _make_bot(code)
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is True
    assert "Patient" in result.log_output
    assert "p-001" in result.log_output


# ── Error handling ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_error_code_returns_failure() -> None:
    executor = BotExecutor()
    bot = _make_bot("raise RuntimeError('test error')")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is False
    assert result.error_message is not None
    assert "RuntimeError" in result.error_message


@pytest.mark.asyncio
async def test_execute_syntax_error_returns_failure() -> None:
    executor = BotExecutor()
    bot = _make_bot("def broken(:")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is False
    assert result.error_message is not None


# ── EventMetadata ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_with_event_metadata() -> None:
    meta = EventMetadata(
        subscription_id="sub-xyz",
        interaction="create",
        resource_type="Patient",
        resource_id="p-001",
        tenant_id="tenant-test",
    )
    executor = BotExecutor()
    bot = _make_bot("print(event.interaction)")
    result = await executor.execute(bot, PATIENT_RESOURCE, event_metadata=meta)
    assert result.success is True
    assert "create" in result.log_output
    assert result.subscription_id == "sub-xyz"
    assert result.interaction == "create"


@pytest.mark.asyncio
async def test_event_metadata_defaults_when_not_provided() -> None:
    executor = BotExecutor()
    bot = _make_bot("pass")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    # No error — default EventMetadata used
    assert result.success is True
    assert result.tenant_id == "tenant-test"


# ── Secrets ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_without_secrets() -> None:
    executor = BotExecutor()
    bot = _make_bot("print('no secrets needed')")
    result = await executor.execute(bot, PATIENT_RESOURCE, encrypted_secrets=None)
    assert result.success is True


@pytest.mark.asyncio
async def test_execute_with_invalid_secrets_does_not_crash() -> None:
    """Decryption failure should be silent — bot still runs without secrets."""
    executor = BotExecutor()
    bot = _make_bot("print('running')")
    bad_secrets = {"api_key": "not-a-valid-ciphertext"}
    result = await executor.execute(bot, PATIENT_RESOURCE, encrypted_secrets=bad_secrets)
    # Must not raise — secrets simply not available
    assert result.success is True
    assert "running" in result.log_output


# ── FHIR client injected ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fhir_client_injected_in_globals() -> None:
    """Bot code should have access to 'client' in globals."""
    code = "print(type(client).__name__)"
    executor = BotExecutor()
    bot = _make_bot(code)
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is True
    assert "IntelliCareClient" in result.log_output


# ── Timeout ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_timeout_kills_bot() -> None:
    import time as _time
    code = "time.sleep(10)"
    executor = BotExecutor()
    bot = _make_bot(code, timeout=1)
    result = await executor.execute(bot, {"time": _time})
    assert result.success is False


# ── grahame_url param ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grahame_url_param_accepted() -> None:
    executor = BotExecutor(grahame_url="http://custom-grahame:9000")
    bot = _make_bot("print('custom url')")
    result = await executor.execute(bot, PATIENT_RESOURCE)
    assert result.success is True
