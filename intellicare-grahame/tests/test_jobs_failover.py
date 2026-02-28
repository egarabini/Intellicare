import pytest
import sys
from unittest.mock import AsyncMock, patch
from types import ModuleType

mock_redis = ModuleType("redis")
mock_redis_asyncio = ModuleType("redis.asyncio")
mock_redis_asyncio.from_url = AsyncMock()
mock_redis_asyncio.ConnectionError = ConnectionError
mock_redis_asyncio.TimeoutError = TimeoutError
mock_redis.asyncio = mock_redis_asyncio
sys.modules.setdefault("redis", mock_redis)
sys.modules.setdefault("redis.asyncio", mock_redis_asyncio)

from app.jobs.failover import BullMQWorkerWithFailover, FailoverConfig, RedisFailoverHandler, aioredis


@pytest.mark.asyncio
async def test_failover_handler_connect_success_sets_state() -> None:
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)

    with patch("app.jobs.failover.aioredis.from_url", new=AsyncMock(return_value=redis_mock)):
        handler = RedisFailoverHandler("redis://localhost:6379/0")
        redis = await handler.connect()

    assert redis is redis_mock
    assert handler.is_connected is True
    assert handler.retry_count == 0


@pytest.mark.asyncio
async def test_failover_handler_execute_with_retry_recovers_once() -> None:
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)

    with patch("app.jobs.failover.aioredis.from_url", new=AsyncMock(return_value=redis_mock)):
        handler = RedisFailoverHandler(
            "redis://localhost:6379/0",
            config=FailoverConfig(initial_delay_seconds=0, max_retries=2),
        )
        await handler.connect()

    state = {"calls": 0}

    async def flaky_operation(_redis):
        state["calls"] += 1
        if state["calls"] == 1:
            raise aioredis.ConnectionError("simulated drop")
        return "ok"

    with patch.object(handler, "_handle_connection_loss", new=AsyncMock()) as reconnect_mock:
        result = await handler.execute_with_retry(flaky_operation)

    assert result == "ok"
    assert reconnect_mock.await_count == 1
    assert state["calls"] == 2


@pytest.mark.asyncio
async def test_worker_move_to_dlq_uses_failover_execute_with_retry() -> None:
    async def processor(_job):
        return None

    worker = BullMQWorkerWithFailover(
        queue_name="notifications",
        processor=processor,
        redis_url="redis://localhost:6379/0",
    )

    with patch.object(
        worker._failover_handler, "execute_with_retry", new=AsyncMock(return_value=None)
    ) as execute_mock:
        await worker._move_to_dlq({"id": "job-1", "attemptsMade": 3}, "boom")

    assert execute_mock.await_count == 1
    call_args = execute_mock.await_args
    assert call_args.args[1] == "notifications:dlq"
    assert "job-1" in call_args.args[2]
    assert "boom" in call_args.args[2]
