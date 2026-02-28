"""Integration-style tests for orchestrator with phase 4 enabled."""

from __future__ import annotations

import pytest

from wanda.config import WandaConfig
from wanda.discovery.models import ModuleInfo, ModuleResponse, ModuleStatus, RoutingDecision
from wanda.orchestrator.orchestrator import WandaOrchestrator


class _FakeRegistry:
    def __init__(self) -> None:
        self._calls = 0
        self._module = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://fake",
            capabilities=["chronic-disease-monitoring"],
            status=ModuleStatus.ONLINE,
        )

    async def discover(self):
        return [self._module]

    @property
    def online_count(self) -> int:
        return 1

    def get_online_modules(self):
        return [self._module]

    def get_module(self, name: str):
        return self._module if name == self._module.name else None

    async def call_module(self, module_name: str, endpoint: str, method: str = "GET", payload=None, params=None):
        _ = module_name, endpoint, method, payload, params
        self._calls += 1
        return ModuleResponse(
            module_name="intellicare-oswaldo",
            endpoint="/api/v1/analyze",
            status_code=0,
            error="downstream timeout",
        )


@pytest.mark.asyncio
async def test_orchestrator_phase4_retry_fallback_trace_and_metrics() -> None:
    registry = _FakeRegistry()
    config = WandaConfig(
        enable_resilience=True,
        enable_metrics=True,
        enable_decision_tracing=True,
        cb_failure_threshold=2,
    )
    orchestrator = WandaOrchestrator(config=config, registry=registry)  # type: ignore[arg-type]

    orchestrator.router.route = lambda query, available_modules, patient_id=None: RoutingDecision(
        target_modules=["intellicare-oswaldo"],
        reason="test",
        confidence=1.0,
        routing_method="keyword",
    )

    result = await orchestrator.chat("como esta o paciente renal", patient_id="p-1")

    assert len(result.responses) == 1
    assert result.responses[0].status_code == 503
    assert "fallback" in result.responses[0].data
    assert registry._calls >= 2  # retry should run more than once

    traces = await orchestrator.trace_store.search(limit=10)  # type: ignore[union-attr]
    assert len(traces) >= 1
    metrics_text = orchestrator.metrics_registry.render().decode("utf-8")  # type: ignore[union-attr]
    assert "wanda_orchestration_requests_total" in metrics_text
