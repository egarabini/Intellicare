"""Admin Router — endpoints REST do modulo admin."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantStatusUpdate,
    TenantUsersResponse,
)
from .service import TenantService

router = APIRouter(tags=["admin"])
_service = TenantService()

AdminRequired = Annotated[TenantContext, Depends(require_role("PLATFORM_ADMIN"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "admin", "version": "1.0.0"}


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    actor: AdminRequired,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> TenantListResponse:
    items, total = await _service.list_tenants(page, size, actor)
    return TenantListResponse(
        items=[TenantResponse(**i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/tenants/{slug}", response_model=TenantResponse)
async def get_tenant(slug: str, actor: AdminRequired) -> TenantResponse:
    tenant = await _service.get_tenant(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' nao encontrado")
    return TenantResponse(**tenant)


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    actor: AdminRequired,
) -> TenantResponse:
    try:
        tenant = await _service.create_tenant(payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return TenantResponse(**tenant)


@router.patch("/tenants/{slug}/status", response_model=TenantResponse)
async def update_tenant_status(
    slug: str,
    update: TenantStatusUpdate,
    actor: AdminRequired,
) -> TenantResponse:
    try:
        tenant = await _service.update_status(slug, update, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return TenantResponse(**tenant)


@router.get("/tenants/{slug}/users", response_model=TenantUsersResponse)
async def list_tenant_users(slug: str, actor: AdminRequired) -> TenantUsersResponse:
    users = await _service.get_tenant_users(slug)
    mapped = [
        {
            "keycloak_id": u["id"],
            "username":    u.get("username", ""),
            "email":       u.get("email", ""),
            "roles":       u.get("realmRoles", []),
            "enabled":     u.get("enabled", True),
        }
        for u in users
    ]
    return TenantUsersResponse(tenant_slug=slug, users=mapped, total=len(mapped))
