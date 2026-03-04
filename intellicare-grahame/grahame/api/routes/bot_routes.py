"""FHIR Bot CRUD + $execute API — intellicare-grahame."""

from __future__ import annotations

from typing import Optional
from grahame.api.deps import get_tenant_session_context

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from grahame.fhir.fhir_error import fhir_error
from grahame.services.bot_service import BotService

router = APIRouter(prefix="/fhir", tags=["FHIR Bots"])

_FHIR_JSON = "application/fhir+json"


def _to_fhir(bot) -> dict:
    return {
        "resourceType": "Bot",
        "id": bot.id,
        "name": bot.name,
        "description": bot.description or "",
        "status": bot.status,
        "runtime": bot.runtime,
        "code": bot.code,
        "codeVersion": bot.code_version,
        "timeoutSeconds": bot.timeout_seconds,
        "meta": {"lastUpdated": bot.updated_at.isoformat() + "Z"},
    }


# ── CRUD ───────────────────────────────────────────────────────────────────


@router.post("/Bot", status_code=201)
async def create_bot(request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    if not body.get("name"):
        return fhir_error(400, "required", "Bot.name is required")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        bot = await svc.create(body)
    return JSONResponse(content=_to_fhir(bot), status_code=201, media_type=_FHIR_JSON)


@router.get("/Bot")
async def list_bots(
    request: Request,
    status: Optional[str] = Query(None),
    _count: int = Query(50, alias="_count"),
    _offset: int = Query(0, alias="_offset"),
):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        bots = await svc.list(status=status, limit=_count, offset=_offset)
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(bots),
        "entry": [{"resource": _to_fhir(b)} for b in bots],
    }
    return JSONResponse(content=bundle, media_type=_FHIR_JSON)


@router.get("/Bot/{bot_id}")
async def get_bot(bot_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        bot = await svc.get(bot_id)
    if bot is None:
        return fhir_error(404, "not-found", f"Bot/{bot_id} not found")
    return JSONResponse(content=_to_fhir(bot), media_type=_FHIR_JSON)


@router.put("/Bot/{bot_id}")
async def update_bot(bot_id: str, request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        bot = await svc.update(bot_id, body)
    if bot is None:
        return fhir_error(404, "not-found", f"Bot/{bot_id} not found")
    return JSONResponse(content=_to_fhir(bot), media_type=_FHIR_JSON)


@router.delete("/Bot/{bot_id}", status_code=204)
async def delete_bot(bot_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        ok = await svc.delete(bot_id)
    if not ok:
        return fhir_error(404, "not-found", f"Bot/{bot_id} not found")
    return JSONResponse(content=None, status_code=204)


# ── Secrets ────────────────────────────────────────────────────────────────


@router.put("/Bot/{bot_id}/secrets/{secret_name}", status_code=200)
async def set_bot_secret(bot_id: str, secret_name: str, request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    value = body.get("value")
    if not value:
        return fhir_error(400, "required", "Secret value required in body.value")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        await svc.set_secret(bot_id, secret_name, value)
    return JSONResponse(content={"ok": True, "name": secret_name}, status_code=200)


# ── $execute ───────────────────────────────────────────────────────────────


@router.post("/Bot/{bot_id}/$execute")
async def execute_bot(bot_id: str, request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    input_resource = body.get("resource", body)

    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        try:
            result = await svc.execute(bot_id, input_resource)
        except ValueError as exc:
            return fhir_error(404, "not-found", str(exc))
        except RuntimeError as exc:
            return fhir_error(500, "exception", str(exc))

    return JSONResponse(content=result, media_type=_FHIR_JSON)


# ── Execution history ──────────────────────────────────────────────────────


@router.get("/Bot/{bot_id}/executions")
async def list_bot_executions(
    bot_id: str,
    request: Request,
    _count: int = Query(20, alias="_count"),
):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    async with get_tenant_session_context(request) as session:
        svc = BotService(session, tenant_id)
        executions = await svc.list_executions(bot_id, limit=_count)

    entries = [
        {
            "id": e.id,
            "botId": e.bot_id,
            "success": e.success,
            "interaction": e.interaction,
            "resourceType": e.input_resource_type,
            "resourceId": e.input_resource_id,
            "durationMs": e.duration_ms,
            "logOutput": e.log_output,
            "errorMessage": e.error_message,
            "createdAt": e.created_at.isoformat() + "Z",
        }
        for e in executions
    ]
    return JSONResponse(
        content={"total": len(entries), "entries": entries}, media_type=_FHIR_JSON
    )
