"""Billing API routes — /admin/billing/*"""

from typing import Optional
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.billing import BillingRecord
from admin.models.tenant import Tenant
from admin.schemas.billing_schemas import BillingResponse
from admin.api.deps import get_db as get_session, require_platform_admin

router = APIRouter(prefix="/admin/billing", tags=["Billing"], dependencies=[Depends(require_platform_admin)])


@router.get("", response_model=list[BillingResponse])
async def list_billing(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    payment_status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List billing records across all tenants (paginated)."""
    query = select(BillingRecord)

    if payment_status:
        query = query.where(BillingRecord.payment_status == payment_status)

    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(BillingRecord.created_at.desc())

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def billing_summary(
    session: AsyncSession = Depends(get_session),
):
    """Financial summary across all tenants."""
    # Revenue by status
    status_result = await session.execute(
        select(
            BillingRecord.payment_status,
            func.count(BillingRecord.id),
            func.sum(BillingRecord.amount),
        ).group_by(BillingRecord.payment_status)
    )
    by_status = {
        row[0]: {"count": row[1], "total": float(row[2] or 0)}
        for row in status_result.fetchall()
    }

    # Total revenue (paid only)
    total_paid = sum(
        v["total"] for k, v in by_status.items() if k == "paid"
    )

    # Overdue tenants count
    overdue_count = by_status.get("overdue", {}).get("count", 0)

    return {
        "by_status": by_status,
        "total_revenue": total_paid,
        "overdue_count": overdue_count,
    }


@router.get("/{tenant_id}", response_model=list[BillingResponse])
async def get_tenant_billing(
    tenant_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get billing records for a specific tenant."""
    # Check tenant exists
    tenant = await session.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    )
    if not tenant.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tenant não encontrado")

    result = await session.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id == tenant_id)
        .order_by(BillingRecord.period_start.desc())
    )
    return result.scalars().all()


@router.post("/{tenant_id}/mark-paid")
async def mark_billing_paid(
    tenant_id: str,
    billing_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Mark a billing record as paid."""
    result = await session.execute(
        select(BillingRecord).where(
            BillingRecord.id == billing_id,
            BillingRecord.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Registro de billing não encontrado")

    record.payment_status = "paid"
    record.paid_at = datetime.now(UTC)
    await session.commit()

    return {"success": True, "billing_id": str(record.id), "status": "paid"}
