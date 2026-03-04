from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from gestor.db import get_db
from gestor.services.role_service import RoleService
from gestor.schemas.role_schemas import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, UserRoleCreate
from gestor.middleware import require_permission

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("", response_model=RoleListResponse)
@require_permission("gestor.roles")
async def list_roles(request: Request, db: AsyncSession = Depends(get_db)):
    service = RoleService(db)
    roles = await service.list_roles()
    return RoleListResponse(roles=roles, total=len(roles))

@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@require_permission("gestor.roles")
async def create_role(request: Request, role_in: RoleCreate, db: AsyncSession = Depends(get_db)):
    service = RoleService(db)
    try:
        return await service.create_role(role_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{role_id}", response_model=RoleResponse)
@require_permission("gestor.roles")
async def update_role(request: Request, role_id: UUID, role_in: RoleUpdate, db: AsyncSession = Depends(get_db)):
    service = RoleService(db)
    try:
        role = await service.update_role(role_id, role_in)
        if not role:
            raise HTTPException(status_code=404, detail="Role não encontrada")
        return role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assign/{user_id}", status_code=status.HTTP_201_CREATED)
@require_permission("gestor.roles")
async def assign_role(request: Request, user_id: UUID, assignment: UserRoleCreate, db: AsyncSession = Depends(get_db)):
    service = RoleService(db)
    assigned_by = getattr(request.state, "user_id", None)
    try:
        await service.assign_role_to_user(user_id, assignment.role_id, assigned_by)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Impossível designar role. Verifique as dependências F0.")
