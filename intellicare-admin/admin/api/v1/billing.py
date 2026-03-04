from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from uuid import UUID

from admin.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from admin.schemas.billing import BillingRecordResponse
from admin.services.billing_service import BillingService

router = APIRouter()

@router.get(
    "/estabelecimentos/{tenant_id}/faturamento",
    response_model=List[BillingRecordResponse],
)
async def get_tenant_billing(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Retorna histórico de faturas do estabelecimento.
    Acesso restrito a PLATFORM_ADMIN ou PLATFORM_GESTOR (do próprio tenant).
    """
    billing_service = BillingService(db)
    records = await billing_service.get_billing_history(tenant_id)
    return records

@router.post(
    "/estabelecimentos/{tenant_id}/faturamento/calcular",
    response_model=BillingRecordResponse,
)
async def force_billing_calculation(
    tenant_id: UUID,
    ano: int,
    mes: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Força cálculo de fatura (admin operation).
    """
    billing_service = BillingService(db)
    try:
        record = await billing_service.calculate_monthly_billing(tenant_id, ano, mes)
        await db.commit()
        await db.refresh(record)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/faturamento/{billing_id}/pagar",
    response_model=BillingRecordResponse,
)
async def mark_billing_paid(
    billing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Marca uma fatura como paga.
    Idealmente via webhook do gateway de pagamento (Stripe/Iugu).
    """
    billing_service = BillingService(db)
    record = await billing_service.mark_as_paid(billing_id)
    if not record:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
        
    await db.commit()
    await db.refresh(record)
    return record
