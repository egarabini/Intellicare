"""Tests for ModuleRegistry resilience integration."""

from __future__ import annotations

import pytest
import httpx

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.discovery.registry import ModuleRegistry
from wanda.resilience import CircuitBreakerManager, FallbackManager, RetryPolicy, TimeoutManager


@pytest.fixture
def resilient_registry() -> ModuleRegistry:
    registry = ModuleRegistry(
        module_urls={"mod-a": "http://mod-a:8000"},
        timeout_seconds=2,
    )
    registry.configure_resilience(
        circuit_breaker_manager=CircuitBreakerManager(failure_threshold=1, success_threshold=1, timeout_seconds=10),
        retry_policy=RetryPolicy(),
        timeout_manager=TimeoutManager(),
        fallback_manager=FallbackManager(),
    )
    registry._modules["mod-a"] = ModuleInfo(
        name="mod-a",
        base_url="http://mod-a:8000",
        status=ModuleStatus.ONLINE,
    )
    return registry


@pytest.mark.asyncio
async def test_registry_resilience_fallback_on_timeout(resilient_registry: ModuleRegistry) -> None:
    class _TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            raise httpx.TimeoutException("timeout")

        async def post(self, *args, **kwargs):
            raise httpx.TimeoutException("timeout")

    original_client = httpx.AsyncClient
    httpx.AsyncClient = _TimeoutClient
    try:
        response = await resilient_registry.call_module("mod-a", "/api/v1/slow")
    finally:
        httpx.AsyncClient = original_client

    assert response.status_code == 503
    assert "fallback" in response.data


@pytest.mark.asyncio
async def test_registry_has_resilience_property(resilient_registry: ModuleRegistry) -> None:
    assert resilient_registry.has_resilience is True
