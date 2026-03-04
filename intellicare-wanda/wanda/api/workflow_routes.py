"""API routes for LangGraph workflows (EF-W005)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class WorkflowExecuteRequest(BaseModel):
    workflow_name: Optional[str] = None
    query: str
    patient_id: Optional[str] = None
    intent: Optional[str] = None
    is_critical: bool = False
    extra: dict = {}


def _get_executor(request: Request):  # type: ignore[return]
    executor = getattr(request.app.state, "workflow_executor", None)
    if executor is None:
        raise HTTPException(status_code=503, detail="WorkflowExecutor nao disponivel (enable_langgraph=False)")
    return executor


@router.post("/execute", summary="Executa um workflow LangGraph")
async def execute_workflow(body: WorkflowExecuteRequest, request: Request):
    executor = _get_executor(request)

    # Select workflow if not specified
    workflow_name = body.workflow_name
    if not workflow_name:
        workflow_name = executor.select_workflow(
            intent=body.intent or "",
            has_patient=bool(body.patient_id),
            is_critical=body.is_critical,
        )
        if not workflow_name:
            raise HTTPException(status_code=400, detail="Nenhum workflow adequado encontrado")

    result = await executor.execute(
        workflow_name=workflow_name,
        query=body.query,
        tenant_id=request.headers.get("X-Tenant-ID", "default"),
        patient_id=body.patient_id,
        extra=body.extra,
    )
    return {
        "workflow_id": result.workflow_id,
        "workflow_name": result.workflow_name,
        "execution_id": result.execution_id,
        "success": result.success,
        "synthesis": result.synthesis,
        "key_points": result.key_points,
        "agent_responses": result.agent_responses,
        "error": result.error,
        "latency_ms": result.latency_ms,
        "iterations": result.iterations,
    }


@router.get("/status/{execution_id}", summary="Status/resultado de um workflow")
async def workflow_status(execution_id: str, request: Request):
    executor = _get_executor(request)
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    state = await executor._checkpointer.restore(tenant_id, execution_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} nao encontrada")
    return {"execution_id": execution_id, "state": state}


@router.get("/available", summary="Lista workflows disponíveis")
async def list_workflows(request: Request):
    executor = _get_executor(request)
    return {"workflows": executor.available_workflows()}
