"""Admin Router — endpoints REST do modulo admin."""
from __future__ import annotations

from typing import Annotated

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import (
    AuditLogResponse,
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantStatusUpdate,
    TenantUpdateRequest,
    TenantUsersResponse,
    UserInviteRequest,
    UserInviteResponse,
)
from .service import TenantService

router = APIRouter(tags=["admin"])
_service = TenantService()

AdminRequired = Annotated[TenantContext, Depends(require_role("PLATFORM_ADMIN"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "admin", "version": "1.0.0"}


@router.get("/dashboard/stats")
async def dashboard_stats(
    actor: AdminRequired,
) -> dict:
    return await _service.get_dashboard_stats()


@router.get("/audit", response_model=AuditLogResponse)
async def audit_log(
    actor: AdminRequired,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    from_date: datetime | None = None,
) -> AuditLogResponse:
    result = await _service.get_audit_log(page, size, action, from_date)
    return AuditLogResponse(**result)


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


@router.patch("/tenants/{slug}", response_model=TenantResponse)
async def update_tenant(
    slug: str,
    body: TenantUpdateRequest,
    actor: AdminRequired,
) -> TenantResponse:
    try:
        tenant = await _service.update_tenant(slug, body, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return TenantResponse(**tenant)


@router.delete("/tenants/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    slug: str,
    actor: AdminRequired,
) -> None:
    await _service.delete_tenant(slug, actor)


@router.post("/tenants/{slug}/users/invite",
             response_model=UserInviteResponse,
             status_code=status.HTTP_201_CREATED)
async def invite_user(
    slug: str,
    body: UserInviteRequest,
    actor: AdminRequired,
) -> UserInviteResponse:
    try:
        result = await _service.invite_user(slug, body, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return UserInviteResponse(**result)


@router.patch("/tenants/{slug}/users/{user_id}/deactivate",
              status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    slug: str,
    user_id: str,
    actor: AdminRequired,
) -> None:
    await _service.deactivate_user(slug, user_id, actor)
