"""Tenant API routes — /admin/tenants/*"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from admin.schemas.tenant_schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse, ModuleUpdate, TenantModuleResponse,
)
from admin.services.tenant_service import TenantService
from admin.services.provisioning_service import ProvisioningService
from admin.api.deps import get_tenant_service, get_provisioning_service, get_actor_id, require_platform_admin

router = APIRouter(prefix="/admin/tenants", tags=["Tenants"], dependencies=[Depends(require_platform_admin)])


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
    provisioning: ProvisioningService = Depends(get_provisioning_service),
    actor_id: str = Depends(get_actor_id),
):
    """Create a new tenant + trigger provisioning."""
    try:
        tenant = await service.create(data, actor_id=actor_id)
    except ValueError as e:
        if "já cadastrado" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # Trigger async provisioning
    result = await provisioning.provision(tenant)
    if not result.success:
        # Tenant was created but provisioning failed — log but don't fail the request
        pass

    # Reload entity with relationships eagerly loaded to avoid async lazy-load on serialization.
    reloaded = await service.get(str(tenant.id))
    return reloaded or tenant


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    service: TenantService = Depends(get_tenant_service),
):
    """List tenants with pagination and filters."""
    return await service.list_tenants(page=page, size=size, status_filter=status, search=search)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
):
    """Get tenant details."""
    tenant = await service.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
    actor_id: str = Depends(get_actor_id),
):
    """Update tenant fields."""
    tenant = await service.update(tenant_id, data, actor_id=actor_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str = Query(..., min_length=5),
    service: TenantService = Depends(get_tenant_service),
    actor_id: str = Depends(get_actor_id),
):
    """Suspend a tenant."""
    tenant = await service.suspend(tenant_id, reason=reason, actor_id=actor_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return {"success": True, "tenant_id": tenant_id, "status": "suspended"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    actor_id: str = Depends(get_actor_id),
):
    """Reactivate a suspended tenant."""
    tenant = await service.activate(tenant_id, actor_id=actor_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return {"success": True, "tenant_id": tenant_id, "status": "active"}


@router.get("/{tenant_id}/modules", response_model=list[TenantModuleResponse])
async def get_tenant_modules(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
):
    """Get modules for a tenant."""
    tenant = await service.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant.modules


@router.patch("/{tenant_id}/modules", response_model=list[TenantModuleResponse])
async def update_tenant_modules(
    tenant_id: str,
    modules: list[ModuleUpdate],
    service: TenantService = Depends(get_tenant_service),
    actor_id: str = Depends(get_actor_id),
):
    """Enable/disable modules for a tenant."""
    try:
        return await service.update_modules(tenant_id, modules, actor_id=actor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
