"""Rotas de roles e RBAC — 3 endpoints."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db, get_audit
from gestor.schemas.role_schemas import RoleCreate, RoleResponse, RoleUpdate
from gestor.services.audit_service import AuditService
from gestor.services.role_service import RoleService

router = APIRouter()


def _role_service(session: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(session)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(svc: RoleService = Depends(_role_service)):
    return await svc.list_roles()


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    data: RoleCreate,
    request: Request,
    svc: RoleService = Depends(_role_service),
    audit: AuditService = Depends(get_audit),
):
    role = await svc.create_role(data)
    await audit.log_action(
        "role.created",
        resource_type="role",
        resource_id=str(role.id),
        details={"name": role.name, "permissions": role.permissions},
        ip_address=request.client.host if request.client else None,
    )
    return role


@router.patch("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    data: RoleUpdate,
    request: Request,
    svc: RoleService = Depends(_role_service),
    audit: AuditService = Depends(get_audit),
):
    role = await svc.update_role(role_id, data)
    await audit.log_action(
        "role.updated",
        resource_type="role",
        resource_id=str(role_id),
        details=data.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )
    return role
