"""Custom Operations routes for tenant-defined FHIR operation execution."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.fhir_error import fhir_error
from grahame.services.custom_ops_service import CustomOpsService
from grahame.services.fhir_service import FHIRService

from ..deps import get_db

fhir_custom_ops_router = APIRouter(prefix="/fhir", tags=["FHIR Custom Operations"])
admin_custom_ops_router = APIRouter(prefix="/admin/custom-operations", tags=["Custom Operations Admin"])

FHIR_MEDIA_TYPE = "application/fhir+json"


def _tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")


def _serialize_operation(op) -> dict[str, Any]:
    return {
        "id": op.id,
        "tenantId": op.tenant_id,
        "name": op.name,
        "type": op.op_type,
        "resourceType": op.resource_type,
        "handlerType": op.handler_type,
        "handlerConfig": op.handler_config,
        "timeoutSeconds": op.timeout_seconds,
        "rateLimitPerMinute": op.rate_limit_per_minute,
        "createdAt": op.created_at.isoformat() + "Z",
        "updatedAt": op.updated_at.isoformat() + "Z",
    }


async def _body_or_empty_parameters(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if not raw:
        return {"resourceType": "Parameters", "parameter": []}
    body = await request.json()
    if not isinstance(body, dict):
        return {"resourceType": "Parameters", "parameter": []}
    return body


# ── Admin CRUD ────────────────────────────────────────────────────────────────


@admin_custom_ops_router.get("")
async def list_custom_operations(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = CustomOpsService(session, _tenant_id(request), request=request)
    items = await svc.list()
    return {"total": len(items), "items": [_serialize_operation(i) for i in items]}


@admin_custom_ops_router.post("", status_code=201)
async def create_custom_operation(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        svc = CustomOpsService(session, _tenant_id(request), request=request)
        op = await svc.create(body)
        return JSONResponse(content=_serialize_operation(op), status_code=201)
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return fhir_error(exc.status_code, "invalid", str(exc.detail))
        return fhir_error(500, "exception", str(exc))


@admin_custom_ops_router.get("/{operation_id}")
async def get_custom_operation(
    operation_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = CustomOpsService(session, _tenant_id(request), request=request)
    op = await svc.get(operation_id)
    if op is None:
        return fhir_error(404, "not-found", f"Custom operation {operation_id} not found")
    return _serialize_operation(op)


@admin_custom_ops_router.put("/{operation_id}")
async def update_custom_operation(
    operation_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        svc = CustomOpsService(session, _tenant_id(request), request=request)
        op = await svc.update(operation_id, body)
        if op is None:
            return fhir_error(404, "not-found", f"Custom operation {operation_id} not found")
        return _serialize_operation(op)
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return fhir_error(exc.status_code, "invalid", str(exc.detail))
        return fhir_error(500, "exception", str(exc))


@admin_custom_ops_router.delete("/{operation_id}", status_code=204)
async def delete_custom_operation(
    operation_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = CustomOpsService(session, _tenant_id(request), request=request)
    ok = await svc.delete(operation_id)
    if not ok:
        return fhir_error(404, "not-found", f"Custom operation {operation_id} not found")
    return JSONResponse(status_code=204, content=None)


# ── FHIR execution routes ─────────────────────────────────────────────────────


@fhir_custom_ops_router.post("/{resource_type}/{resource_id}/${operation_name}")
async def execute_instance_custom_operation(
    resource_type: str,
    resource_id: str,
    operation_name: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    tenant_id = _tenant_id(request)
    svc = CustomOpsService(session, tenant_id, request=request)
    operation = await svc.lookup(operation_name, resource_type)
    if operation is None or operation.op_type != "instance":
        return fhir_error(404, "not-found", f"Custom operation '{operation_name}' not registered for {resource_type}")

    fhir_service = FHIRService(session, tenant_id=tenant_id)
    try:
        resource_row = await fhir_service.get(resource_type, resource_id)
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return fhir_error(exc.status_code, "not-found", str(exc.detail))
        return fhir_error(500, "exception", str(exc))

    payload = await _body_or_empty_parameters(request)
    try:
        result = await svc.execute(
            operation,
            payload,
            resource=resource_row.resource,
            resource_id=resource_id,
        )
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return fhir_error(exc.status_code, "processing", str(exc.detail))
        return fhir_error(500, "exception", str(exc))
    return JSONResponse(content=result, media_type=FHIR_MEDIA_TYPE)


@fhir_custom_ops_router.post("/${operation_name}")
async def execute_system_custom_operation(
    operation_name: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = CustomOpsService(session, _tenant_id(request), request=request)
    operation = await svc.lookup(operation_name)
    if operation is None or operation.op_type != "system":
        return fhir_error(404, "not-found", f"Custom operation '{operation_name}' not registered")

    payload = await _body_or_empty_parameters(request)
    try:
        result = await svc.execute(operation, payload, resource=None)
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return fhir_error(exc.status_code, "processing", str(exc.detail))
        return fhir_error(500, "exception", str(exc))
    return JSONResponse(content=result, media_type=FHIR_MEDIA_TYPE)
