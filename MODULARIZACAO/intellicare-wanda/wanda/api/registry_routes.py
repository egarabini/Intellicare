"""Registry API routes — /api/v1/registry/* (EF-W001).

Endpoints for querying the persistent module registry,
health history, capabilities history, and routing table.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])

# These will be set by app.py during startup
_registry = None
_discovery = None


def init_registry_routes(registry, discovery) -> None:
    """Initialize dependencies (called from app.py)."""
    global _registry, _discovery
    _registry = registry
    _discovery = discovery


@router.get("")
async def list_all_modules():
    """Full registry of all registered modules."""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    modules = await _registry.get_all_modules_dict()
    return {
        "success": True,
        "data": {
            "total": _registry.total_modules,
            "online": _registry.online_count,
            "has_persistence": _registry.has_persistence,
            "modules": modules,
        },
    }


@router.get("/routing-table")
async def routing_table():
    """Current routing table derived from active modules."""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    table = await _registry.get_routing_table()
    return {"success": True, "data": table}


@router.get("/{agent_name}")
async def get_module_detail(agent_name: str):
    """Details of a specific registered module."""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    module = _registry.get_module(agent_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {agent_name} not found")

    return {
        "success": True,
        "data": module.to_dict(),
    }


@router.get("/{agent_name}/history")
async def get_module_health_history(
    agent_name: str,
    limit: int = Query(default=50, ge=1, le=500),
):
    """Health event history for a module."""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    history = await _registry.get_health_history(agent_name, last_n_events=limit)
    return {
        "success": True,
        "data": {
            "agent_name": agent_name,
            "events": history,
            "count": len(history),
        },
    }


@router.get("/{agent_name}/capabilities-history")
async def get_capabilities_history(
    agent_name: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Capabilities version history for a module."""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    history = await _registry.get_capabilities_history(agent_name, last_n=limit)
    return {
        "success": True,
        "data": {
            "agent_name": agent_name,
            "versions": history,
            "count": len(history),
        },
    }
