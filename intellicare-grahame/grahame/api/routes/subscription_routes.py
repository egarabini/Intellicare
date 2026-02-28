"""FHIR Subscription CRUD API — intellicare-grahame."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from grahame.fhir.fhir_error import fhir_error
from grahame.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/fhir", tags=["FHIR Subscriptions"])

_FHIR_JSON = "application/fhir+json"


def _to_fhir(sub) -> dict:
    """Serialise ORM Subscription to FHIR Subscription resource dict."""
    header_list: list[str] = []
    if sub.channel_header:
        header_list = [f"{k}: {v}" for k, v in sub.channel_header.items()]
    return {
        "resourceType": "Subscription",
        "id": sub.id,
        "status": sub.status,
        "reason": sub.reason or "",
        "criteria": sub.criteria,
        "channel": {
            "type": sub.channel_type,
            "endpoint": sub.channel_endpoint,
            "payload": sub.channel_payload or "application/fhir+json",
            "header": header_list,
        },
        "meta": {
            "lastUpdated": sub.updated_at.isoformat() + "Z",
            "versionId": "1",
        },
    }


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/Subscription", status_code=201)
async def create_subscription(request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")

    data = {
        "status": body.get("status", "requested"),
        "criteria": body.get("criteria", ""),
        "reason": body.get("reason"),
        "channel": body.get("channel", {}),
    }
    if not data["criteria"]:
        return fhir_error(400, "required", "Subscription.criteria is required")
    if not data["channel"].get("type"):
        return fhir_error(400, "required", "Subscription.channel.type is required")

    session = request.app.state.session_factory()
    async with session:
        svc = SubscriptionService(session, tenant_id)
        try:
            sub = await svc.create(data)
        except ValueError as exc:
            return fhir_error(429, "too-costly", str(exc))

    return JSONResponse(content=_to_fhir(sub), status_code=201, media_type=_FHIR_JSON)


@router.get("/Subscription")
async def list_subscriptions(
    request: Request,
    status: Optional[str] = Query(None),
    _count: int = Query(50, alias="_count"),
    _offset: int = Query(0, alias="_offset"),
):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    session = request.app.state.session_factory()
    async with session:
        svc = SubscriptionService(session, tenant_id)
        subs = await svc.list(status=status, limit=_count, offset=_offset)

    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(subs),
        "entry": [{"resource": _to_fhir(s)} for s in subs],
    }
    return JSONResponse(content=bundle, media_type=_FHIR_JSON)


@router.get("/Subscription/{subscription_id}")
async def get_subscription(subscription_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    session = request.app.state.session_factory()
    async with session:
        svc = SubscriptionService(session, tenant_id)
        sub = await svc.get(subscription_id)

    if sub is None:
        return fhir_error(404, "not-found", f"Subscription/{subscription_id} not found")
    return JSONResponse(content=_to_fhir(sub), media_type=_FHIR_JSON)


@router.put("/Subscription/{subscription_id}")
async def update_subscription(subscription_id: str, request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")

    data: dict = {}
    for field in ("status", "criteria", "reason"):
        if field in body:
            data[field] = body[field]
    if "channel" in body:
        data["channel"] = body["channel"]

    session = request.app.state.session_factory()
    async with session:
        svc = SubscriptionService(session, tenant_id)
        sub = await svc.update(subscription_id, data)

    if sub is None:
        return fhir_error(404, "not-found", f"Subscription/{subscription_id} not found")
    return JSONResponse(content=_to_fhir(sub), media_type=_FHIR_JSON)


@router.delete("/Subscription/{subscription_id}", status_code=204)
async def delete_subscription(subscription_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    session = request.app.state.session_factory()
    async with session:
        svc = SubscriptionService(session, tenant_id)
        ok = await svc.delete(subscription_id)

    if not ok:
        return fhir_error(404, "not-found", f"Subscription/{subscription_id} not found")
    return JSONResponse(content=None, status_code=204)
