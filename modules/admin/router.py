"""Admin Router — endpoints REST do modulo admin."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import (
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    AuditLogResponse,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    FinanceiroDashboard,
    InvoiceOut,
    InvoiceStatusUpdate,
    ModuleOut,
    ModuleStatusUpdate,
    PagedResponse,
    ServerCreate,
    ServerOut,
    ServerUpdate,
    TenantCreate,
    TenantListResponse,
    TenantModuleOut,
    TenantModuleUpdate,
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
async def health() -> dict[str, str]:
    return {"status": "healthy", "module": "admin", "version": "1.0.0"}


@router.get("/dashboard/stats")
async def dashboard_stats(actor: AdminRequired) -> dict:
    del actor
    return await _service.get_dashboard_stats()


@router.get("/audit", response_model=AuditLogResponse)
async def audit_log(
    actor: AdminRequired,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    from_date: datetime | None = None,
) -> AuditLogResponse:
    del actor
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
        items=[TenantResponse(**item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/tenants/{slug}", response_model=TenantResponse)
async def get_tenant(slug: str, actor: AdminRequired) -> TenantResponse:
    del actor
    tenant = await _service.get_tenant(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' nao encontrado")
    return TenantResponse(**tenant)


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, actor: AdminRequired) -> TenantResponse:
    try:
        tenant = await _service.create_tenant(payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
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
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TenantResponse(**tenant)


@router.get("/tenants/{slug}/users", response_model=TenantUsersResponse)
async def list_tenant_users(slug: str, actor: AdminRequired) -> TenantUsersResponse:
    del actor
    users = await _service.get_tenant_users(slug)
    mapped = [
        {
            "keycloak_id": user["id"],
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "roles": user.get("realmRoles", []),
            "enabled": user.get("enabled", True),
        }
        for user in users
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
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TenantResponse(**tenant)


@router.delete("/tenants/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(slug: str, actor: AdminRequired) -> None:
    await _service.delete_tenant(slug, actor)


@router.post(
    "/tenants/{slug}/users/invite",
    response_model=UserInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_user(
    slug: str,
    body: UserInviteRequest,
    actor: AdminRequired,
) -> UserInviteResponse:
    try:
        result = await _service.invite_user(slug, body, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return UserInviteResponse(**result)


@router.patch("/tenants/{slug}/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(slug: str, user_id: str, actor: AdminRequired) -> None:
    await _service.deactivate_user(slug, user_id, actor)


@router.get("/servers", response_model=list[ServerOut])
async def list_servers(actor: AdminRequired) -> list[ServerOut]:
    del actor
    return [ServerOut(**item) for item in await _service.list_servers()]


@router.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(payload: ServerCreate, actor: AdminRequired) -> ServerOut:
    server = await _service.create_server(payload, actor)
    return ServerOut(**server)


@router.patch("/servers/{server_id}", response_model=ServerOut)
async def update_server(server_id: int, payload: ServerUpdate, actor: AdminRequired) -> ServerOut:
    try:
        server = await _service.update_server(server_id, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ServerOut(**server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: int, actor: AdminRequired) -> None:
    try:
        await _service.delete_server(server_id, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/modules", response_model=list[ModuleOut])
async def list_modules(actor: AdminRequired) -> list[ModuleOut]:
    del actor
    return [ModuleOut(**item) for item in await _service.list_modules()]


@router.patch("/modules/{slug}/status", response_model=ModuleOut)
async def update_module_status(
    slug: str,
    payload: ModuleStatusUpdate,
    actor: AdminRequired,
) -> ModuleOut:
    try:
        module = await _service.update_module_status(slug, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ModuleOut(**module)


@router.get("/tenants/{slug}/modules", response_model=list[TenantModuleOut])
async def list_tenant_modules(slug: str, actor: AdminRequired) -> list[TenantModuleOut]:
    del actor
    return [TenantModuleOut(**item) for item in await _service.list_tenant_modules(slug)]


@router.patch("/tenants/{slug}/modules/{module_slug}", response_model=TenantModuleOut)
async def update_tenant_module(
    slug: str,
    module_slug: str,
    payload: TenantModuleUpdate,
    actor: AdminRequired,
) -> TenantModuleOut:
    try:
        item = await _service.update_tenant_module(slug, module_slug, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TenantModuleOut(**item)


@router.get("/financeiro/dashboard", response_model=FinanceiroDashboard)
async def financeiro_dashboard(actor: AdminRequired) -> FinanceiroDashboard:
    del actor
    return FinanceiroDashboard(**(await _service.get_financeiro_dashboard()))


@router.get("/invoices", response_model=PagedResponse)
async def list_invoices(
    actor: AdminRequired,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    tenant_slug: str | None = None,
) -> PagedResponse:
    del actor
    result = await _service.list_invoices(page, size, status, tenant_slug)
    return PagedResponse(**result)


@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceOut)
async def update_invoice_status(
    invoice_id: str,
    payload: InvoiceStatusUpdate,
    actor: AdminRequired,
) -> InvoiceOut:
    try:
        invoice = await _service.update_invoice_status(invoice_id, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InvoiceOut(**invoice)


@router.get("/expenses", response_model=PagedResponse)
async def list_expenses(
    actor: AdminRequired,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PagedResponse:
    del actor
    result = await _service.list_expenses(page, size)
    return PagedResponse(**result)


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(payload: ExpenseCreate, actor: AdminRequired) -> ExpenseOut:
    expense = await _service.create_expense(payload, actor)
    return ExpenseOut(**expense)


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    actor: AdminRequired,
) -> ExpenseOut:
    try:
        expense = await _service.update_expense(expense_id, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExpenseOut(**expense)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, actor: AdminRequired) -> None:
    try:
        await _service.delete_expense(expense_id, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/users", response_model=list[AdminUserOut])
async def list_admin_users(actor: AdminRequired) -> list[AdminUserOut]:
    del actor
    return [AdminUserOut(**item) for item in await _service.list_admin_users()]


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_admin_user(payload: AdminUserCreate, actor: AdminRequired) -> AdminUserOut:
    user = await _service.create_admin_user(payload, actor)
    return AdminUserOut(**user)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_admin_user(
    user_id: int,
    payload: AdminUserUpdate,
    actor: AdminRequired,
) -> AdminUserOut:
    try:
        user = await _service.update_admin_user(user_id, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminUserOut(**user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(user_id: int, actor: AdminRequired) -> None:
    try:
        await _service.delete_admin_user(user_id, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
