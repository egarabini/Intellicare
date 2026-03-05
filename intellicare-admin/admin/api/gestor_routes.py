import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from admin.api.deps import get_db, require_platform_admin
from admin.models.tenant_gestor import TenantGestor
from pydantic import BaseModel, EmailStr

router = APIRouter(tags=["Gestores"], dependencies=[Depends(require_platform_admin)])
logger = logging.getLogger(__name__)

class TenantGestorCreate(BaseModel):
    nome: str
    email: EmailStr
    telefone: str | None = None

class GestorResponse(BaseModel):
    id: UUID
    tenant_id: str
    keycloak_user_id: str
    nome: str
    email: str
    telefone: str | None
    active: bool

    class Config:
        from_attributes = True

@router.get("/tenants/{tenant_id}/gestores", response_model=List[GestorResponse])
async def list_gestores(tenant_id: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(TenantGestor).where(TenantGestor.tenant_id == tenant_id, TenantGestor.active == True))
    return result.scalars().all()

@router.post("/tenants/{tenant_id}/gestores", response_model=GestorResponse, status_code=201)
async def create_gestor(tenant_id: str, payload: TenantGestorCreate, session: AsyncSession = Depends(get_db)):
    # 1. Provision user in Keycloak with TENANT_GESTOR role
    # NOTE: KeycloakClient.create_user() not yet implemented in intellicare-auth.
    # For now, generates a local UUID. When Keycloak admin API integration is ready,
    # replace with actual user provisioning.
    import uuid as _uuid
    kc_user_id = str(_uuid.uuid4())
    logger.info("Gestor provisioned with local UUID=%s (Keycloak provisioning pending)", kc_user_id)
    
    gestor = TenantGestor(
        tenant_id=tenant_id,
        keycloak_user_id=kc_user_id,
        nome=payload.nome,
        email=payload.email,
        telefone=payload.telefone
    )
    session.add(gestor)
    await session.commit()
    await session.refresh(gestor)
    return gestor

@router.delete("/tenants/{tenant_id}/gestores/{uid}", status_code=204)
async def remove_gestor(tenant_id: str, uid: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(TenantGestor).where(TenantGestor.id == uid, TenantGestor.tenant_id == tenant_id))
    gestor = result.scalar_one_or_none()
    if not gestor:
        raise HTTPException(status_code=404, detail="Gestor not found")
        
    gestor.active = False
    await session.commit()
    return None
