"""Painel de saude simplificado do ecossistema."""

from __future__ import annotations

from wanda.resilience.circuit_breaker import CircuitBreakerManager
from wanda.resilience.models import CircuitState


class HealthDashboard:
    def __init__(self, circuit_breaker_manager: CircuitBreakerManager) -> None:
        self._manager = circuit_breaker_manager

    async def get_ecosystem_health(self) -> dict[str, object]:
        snapshots = self._manager.snapshots()
        agent_states = {
            snapshot.agent_name: {
                "circuit": snapshot.state.value,
                "failures": snapshot.failures,
                "successes": snapshot.successes,
            }
            for snapshot in snapshots
        }
        overall = "healthy"
        if any(snapshot.state == CircuitState.OPEN for snapshot in snapshots):
            overall = "degraded"
        return {"overall": overall, "agents": agent_states}

    async def get_agent_health(self, agent_name: str) -> dict[str, object]:
        snapshot = self._manager.get(agent_name).snapshot()
        return {
            "agent": agent_name,
            "circuit": snapshot.state.value,
            "failures": snapshot.failures,
            "successes": snapshot.successes,
        }
