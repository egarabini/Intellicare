"""Endpoints de resiliencia (EF-W008)."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["resilience"])

_health_dashboard = None
_cb_manager = None


def init_resilience_routes(health_dashboard=None, circuit_breaker_manager=None) -> None:
    global _health_dashboard, _cb_manager
    _health_dashboard = health_dashboard
    _cb_manager = circuit_breaker_manager


@router.get("/api/v1/health/ecosystem")
async def ecosystem_health():
    if _health_dashboard is None:
        raise HTTPException(status_code=503, detail="Resilience not initialized")
    return await _health_dashboard.get_ecosystem_health()


@router.get("/api/v1/health/agents/{agent_name}")
async def agent_health(agent_name: str):
    if _health_dashboard is None:
        raise HTTPException(status_code=503, detail="Resilience not initialized")
    return await _health_dashboard.get_agent_health(agent_name)


@router.post("/api/v1/circuit/{agent_name}/reset")
async def reset_circuit(agent_name: str):
    if _cb_manager is None:
        raise HTTPException(status_code=503, detail="Resilience not initialized")
    reset_ok = _cb_manager.reset(agent_name)
    if not reset_ok:
        raise HTTPException(status_code=404, detail=f"Circuit breaker de {agent_name} nao encontrado")
    return {"success": True, "agent": agent_name, "state": "CLOSED"}
