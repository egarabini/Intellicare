"""Tests for retry, timeout and fallback components."""

from __future__ import annotations

import pytest

from wanda.discovery.models import ModuleResponse
from wanda.resilience import FallbackManager, RetryPolicy, TimeoutManager


@pytest.mark.asyncio
async def test_retry_policy_retries_until_success() -> None:
    retry = RetryPolicy()
    state = {"attempts": 0}

    async def operation():
        state["attempts"] += 1
        if state["attempts"] < 2:
            raise RuntimeError("temporary")
        return "ok"

    result = await retry.execute_with_retry(operation, policy_name="default")
    assert result == "ok"
    assert state["attempts"] >= 2


def test_timeout_manager_returns_specific_and_default() -> None:
    tm = TimeoutManager()
    assert tm.get_timeout("florence", "analyze") == 45.0
    assert tm.get_timeout("geralda", "analyze") == 30.0
    assert tm.get_timeout("x", "other") == 30.0


@pytest.mark.asyncio
async def test_fallback_manager_partial_response() -> None:
    manager = FallbackManager()
    responses = [
        ModuleResponse(module_name="intellicare-oswaldo", endpoint="/x", status_code=200, data={"message": "A"}),
        ModuleResponse(module_name="intellicare-florence", endpoint="/x", status_code=500, data={}, error="down"),
    ]
    partial = await manager.get_partial_response(successful_responses=responses, failed_agents=["intellicare-florence"])
    assert "aggregated_response" in partial
    assert partial["failed_agents"] == ["intellicare-florence"]
