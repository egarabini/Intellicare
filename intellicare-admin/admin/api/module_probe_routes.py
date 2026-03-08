from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from intellicare_auth import require_role

from admin.services.module_proxy import MODULE_REGISTRY, ModuleProxyClient

router = APIRouter(tags=["Modules"])

@router.get("/admin/modules")
async def list_modules() -> list[dict[str, Any]]:
    """List all registered modules and their health probe (in parallel)."""
    
    # Normally, you'd extract the internal sa token if auth was configured here 
    # but for probe MVP we can proxy without specific credentials 
    # since /health and /info are open in most modules.
    proxy = ModuleProxyClient()
    
    import asyncio
    
    async def _fetch_probe(name: str, config: dict[str, Any]) -> dict[str, Any]:
        probe_result = await proxy.probe(name)
        return {
            "name": name,
            "display_name": config["display_name"],
            "description": config["description"],
            "base_url": config["url"],
            "port": config["port"],
            "probe": probe_result
        }
        
    tasks = [_fetch_probe(name, config) for name, config in MODULE_REGISTRY.items()]
    results = await asyncio.gather(*tasks)
    return list(results)


@router.get("/admin/modules/{name}/probe")
async def probe_module(name: str) -> dict[str, Any]:
    """Probe a single module."""
    if name not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found in registry")
        
    proxy = ModuleProxyClient()
    config = MODULE_REGISTRY[name]
    probe_result = await proxy.probe(name)
    
    return {
        "name": name,
        "display_name": config["display_name"],
        "description": config["description"],
        "base_url": config["url"],
        "port": config["port"],
        "probe": probe_result
    }

