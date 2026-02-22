"""Tests for circuit breaker (EF-W008)."""

from __future__ import annotations

import asyncio

import pytest

from wanda.resilience import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitOpenError,
    CircuitState,
    InMemoryCircuitStateStore,
)


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker("intellicare-oswaldo", failure_threshold=2, timeout_seconds=60)

    async def fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    assert breaker.get_state() == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        await breaker.call(fail)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_and_close() -> None:
    breaker = CircuitBreaker("intellicare-oswaldo", failure_threshold=1, success_threshold=1, timeout_seconds=1)

    async def fail():
        raise RuntimeError("boom")

    async def ok():
        return {"ok": True}

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    assert breaker.get_state() == CircuitState.OPEN
    await asyncio.sleep(1.05)
    result = await breaker.call(ok)
    assert result == {"ok": True}
    assert breaker.get_state() == CircuitState.CLOSED


def test_circuit_breaker_manager_reset() -> None:
    manager = CircuitBreakerManager(failure_threshold=1)
    breaker = manager.get("intellicare-florence")
    assert breaker.agent_name == "intellicare-florence"
    assert manager.reset("nao-existe") is False


@pytest.mark.asyncio
async def test_circuit_breaker_state_persists_with_store() -> None:
    store = InMemoryCircuitStateStore()
    manager1 = CircuitBreakerManager(
        failure_threshold=1,
        success_threshold=1,
        timeout_seconds=60,
        state_store=store,
    )
    breaker1 = manager1.get("intellicare-zilda")

    async def fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker1.call(fail)
    assert breaker1.get_state() == CircuitState.OPEN

    manager2 = CircuitBreakerManager(
        failure_threshold=1,
        success_threshold=1,
        timeout_seconds=60,
        state_store=store,
    )
    breaker2 = manager2.get("intellicare-zilda")
    assert breaker2.get_state() == CircuitState.OPEN
