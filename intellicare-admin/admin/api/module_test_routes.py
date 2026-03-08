from typing import Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from admin.services.module_proxy import MODULE_REGISTRY, ModuleProxyClient
from admin.config.test_payloads import DEFAULT_TEST_PAYLOADS
from admin.db.session import session_factory
from admin.models.module_test_log import ModuleTestLog

# Normally `get_current_user` would come from `intellicare_auth.fastapi` or deps.py
# Using a fallback string for the demo, since auth is enforced via middleware in this app.
router = APIRouter(tags=["Module Tests"])

class TestExecutionRequest(BaseModel):
    payload_key: Optional[str] = "default"
    custom_payload: Optional[dict[str, Any]] = None

@router.post("/admin/modules/{name}/test")
async def run_functional_test(name: str, req: TestExecutionRequest) -> dict[str, Any]:
    """Runs a functional /analyze test with a predefined or custom payload against a target module."""
    if name not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found in registry")
        
    payload = req.custom_payload
    if not payload and req.payload_key == "default":
        payload = DEFAULT_TEST_PAYLOADS.get(name, {})
        
    proxy = ModuleProxyClient()
    result = await proxy.test_analyze(name, payload or {})
    
    # Save test logs to database asynchronously
    async with session_factory.engine.begin() as conn:
        import datetime
        from sqlalchemy import insert
        await conn.execute(
            insert(ModuleTestLog).values(
                module_name=name,
                test_type="functional",
                payload_key=req.payload_key if not req.custom_payload else "custom",
                status_code=result.get("status_code", -1),
                latency_ms=result.get("latency_ms", -1),
                success=result.get("success", False),
                response_json=result.get("response", {}),
                error_message=result.get("error", None),
                triggered_by="admin-user-via-console",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
        )
        
    return {
        "module": name,
        "payload_key": req.payload_key if not req.custom_payload else "custom",
        "request_sent_at": result.get("request_sent_at", ""),
        "latency_ms": result.get("latency_ms"),
        "status_code": result.get("status_code"),
        "success": result.get("success"),
        "response": result.get("response"),
        "error": result.get("error")
    }

@router.get("/admin/modules/{name}/history")
async def get_test_history(name: str) -> list[dict[str, Any]]:
    """Gets the test execution history of a module."""
    from sqlalchemy import select
    
    async with session_factory.engine.begin() as conn:
        res = await conn.execute(
            select(ModuleTestLog)
            .where(ModuleTestLog.module_name == name)
            .order_by(ModuleTestLog.created_at.desc())
            .limit(20)
        )
        logs = res.mappings().all()
        return [dict(l) for l in logs]
