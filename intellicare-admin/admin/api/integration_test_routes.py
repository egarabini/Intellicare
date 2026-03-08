import asyncio
import time
import datetime
from typing import Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from admin.services.module_proxy import MODULE_REGISTRY, ModuleProxyClient
from admin.config.integration_tests import INTEGRATION_FLOWS
from admin.config.test_payloads import DEFAULT_TEST_PAYLOADS
from admin.db.session import session_factory
from admin.models.module_test_log import ModuleTestLog
from sqlalchemy import insert

router = APIRouter(tags=["Integration Tests"])

class IntegrationTestResponse(BaseModel):
    flow_id: str
    status: str
    total_latency_ms: int
    steps_results: List[Any]

@router.get("/admin/integration-flows")
async def list_integration_flows() -> List[dict[str, Any]]:
    """List all defined integration flows for the frontend runner."""
    return list(INTEGRATION_FLOWS.values())

async def execute_step(proxy: ModuleProxyClient, step: dict[str, Any], flow_id: str) -> dict[str, Any]:
    module = step["module"]
    payload_key = step["payload_key"]
    
    if "custom_payload" in step:
        payload = step["custom_payload"]
    elif payload_key == "default":
        payload = DEFAULT_TEST_PAYLOADS.get(module, {})
    else:
        payload = {}

    start = time.monotonic()
    result = await proxy.test_analyze(module, payload)
    latency = int((time.monotonic() - start) * 1000)

    # Note: For genuine integration logs, we will mark test_type="integration" and trigger="flow_id"
    async with session_factory.engine.begin() as conn:
        await conn.execute(
            insert(ModuleTestLog).values(
                module_name=module,
                test_type="integration",
                payload_key=f"flow:{flow_id}:{payload_key}",
                status_code=result.get("status_code", -1),
                latency_ms=result.get("latency_ms", -1) or latency,
                success=result.get("success", False),
                response_json=result.get("response", {}),
                error_message=result.get("error", None),
                triggered_by="admin-user-flow-runner",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
        )

    return {
        "module": module,
        "payload_key": payload_key,
        "success": result.get("success", False),
        "status_code": result.get("status_code", -1),
        "latency_ms": result.get("latency_ms", -1) or latency,
        "response": result.get("response"),
        "error": result.get("error")
    }

@router.post("/admin/integration-flows/{flow_id}/run", response_model=IntegrationTestResponse)
async def run_integration_flow(flow_id: str):
    """Execute a defined integration test flow (sequential or parallel)."""
    if flow_id not in INTEGRATION_FLOWS:
        raise HTTPException(status_code=404, detail="Integration flow not found")
        
    flow = INTEGRATION_FLOWS[flow_id]
    steps = flow["steps"]
    proxy = ModuleProxyClient()
    
    start_time = time.monotonic()
    results = []
    
    if flow["type"] == "parallel":
        tasks = [execute_step(proxy, step, flow_id) for step in steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Convert exceptions to dicts
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                results[i] = {
                    "module": steps[i]["module"],
                    "success": False,
                    "error": str(res),
                    "status_code": 500
                }
    else:
        # Sequential
        for step in steps:
            res = await execute_step(proxy, step, flow_id)
            results.append(res)
            # Short-circuit on sequential failure
            if not res.get("success"):
                break
                
    total_latency = int((time.monotonic() - start_time) * 1000)
    
    overall_success = all(isinstance(r, dict) and r.get("success") for r in results)
    
    return IntegrationTestResponse(
        flow_id=flow_id,
        status="success" if overall_success else "failed",
        total_latency_ms=total_latency,
        steps_results=results
    )
