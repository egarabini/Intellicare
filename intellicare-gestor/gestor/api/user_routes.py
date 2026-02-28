"""Rotas de usuários — 4 endpoints."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db, get_audit
from gestor.schemas.user_schemas import UserCreate, UserResponse, UserUpdate
from gestor.services.audit_service import AuditService
from gestor.services.user_service import UserService

router = APIRouter()


def _user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    active_only: bool = True,
    sector_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    svc: UserService = Depends(_user_service),
):
    return await svc.list_users(active_only=active_only, sector_id=sector_id, limit=limit, offset=offset)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    request: Request,
    svc: UserService = Depends(_user_service),
    audit: AuditService = Depends(get_audit),
):
    user = await svc.create_user(data)
    await audit.log(
        "user.created",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    svc: UserService = Depends(_user_service),
    audit: AuditService = Depends(get_audit),
):
    user = await svc.update_user(user_id, data)
    await audit.log(
        "user.updated",
        resource_type="user",
        resource_id=str(user_id),
        details=data.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.delete("/users/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    svc: UserService = Depends(_user_service),
    audit: AuditService = Depends(get_audit),
):
    user = await svc.deactivate_user(user_id)
    await audit.log(
        "user.deactivated",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=request.client.host if request.client else None,
    )
    return user
