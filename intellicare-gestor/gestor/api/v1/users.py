from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from gestor.db import get_db
from gestor.services.user_service import UserService
from gestor.schemas.user_schemas import TenantUserCreate, TenantUserUpdate, TenantUserResponse, TenantUserListResponse
from gestor.middleware import require_permission

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=TenantUserListResponse)
@require_permission("gestor.usuarios")
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    users = await service.list_users(skip=skip, limit=limit)
    return TenantUserListResponse(users=users, total=len(users))

@router.get("/{user_id}", response_model=TenantUserResponse)
@require_permission("gestor.usuarios")
async def get_user_by_id(request: Request, user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@router.post("", response_model=TenantUserResponse, status_code=status.HTTP_201_CREATED)
@require_permission("gestor.usuarios")
async def create_user(request: Request, user_in: TenantUserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    existing_user = await service.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário com este email já existe no tenant.")
        
    return await service.create_user(user_in)

@router.patch("/{user_id}", response_model=TenantUserResponse)
@require_permission("gestor.usuarios")
async def update_user(request: Request, user_id: UUID, user_in: TenantUserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    updated = await service.update_user(user_id, user_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return updated

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("gestor.usuarios")
async def deactivate_user(request: Request, user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success = await service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
