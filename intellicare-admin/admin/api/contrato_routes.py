import logging
from typing import List
from uuid import UUID
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from admin.api.deps import get_db, require_platform_admin
from admin.models.tenant_contrato import TenantContrato
from pydantic import BaseModel

router = APIRouter(tags=["Contratos"], dependencies=[Depends(require_platform_admin)])
logger = logging.getLogger(__name__)

class TenantContratoCreate(BaseModel):
    plan_id: UUID
    inicio_vigencia: date
    fim_vigencia: date | None = None
    valor_mensal: Decimal
    obs: str | None = None

class ContratoResponse(BaseModel):
    id: UUID
    tenant_id: str
    plan_id: UUID
    inicio_vigencia: date
    fim_vigencia: date | None
    valor_mensal: Decimal
    obs: str | None

    class Config:
        from_attributes = True

@router.get("/tenants/{tenant_id}/contrato", response_model=List[ContratoResponse])
async def list_contratos(tenant_id: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(TenantContrato)
        .where(TenantContrato.tenant_id == tenant_id)
        .order_by(TenantContrato.inicio_vigencia.desc())
    )
    return result.scalars().all()

@router.post("/tenants/{tenant_id}/contrato", response_model=ContratoResponse, status_code=201)
async def create_contrato(tenant_id: str, payload: TenantContratoCreate, session: AsyncSession = Depends(get_db)):
    contrato = TenantContrato(
        tenant_id=tenant_id,
        plan_id=payload.plan_id,
        inicio_vigencia=payload.inicio_vigencia,
        fim_vigencia=payload.fim_vigencia,
        valor_mensal=payload.valor_mensal,
        obs=payload.obs
    )
    session.add(contrato)
    await session.commit()
    await session.refresh(contrato)
    return contrato

@router.patch("/tenants/{tenant_id}/contrato/{contrato_id}", response_model=ContratoResponse)
async def update_contrato(tenant_id: str, contrato_id: UUID, payload: TenantContratoCreate, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(TenantContrato).where(TenantContrato.id == contrato_id, TenantContrato.tenant_id == tenant_id))
    contrato = result.scalar_one_or_none()
    
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato not found")

    contrato.plan_id = payload.plan_id
    contrato.inicio_vigencia = payload.inicio_vigencia
    contrato.fim_vigencia = payload.fim_vigencia
    contrato.valor_mensal = payload.valor_mensal
    contrato.obs = payload.obs
    
    await session.commit()
    await session.refresh(contrato)
    return contrato
