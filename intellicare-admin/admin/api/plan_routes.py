"""Plan and Dashboard API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.plan import Plan
from admin.models.tenant import Tenant
from admin.models.billing import BillingRecord
from admin.schemas.plan_schemas import PlanResponse
from admin.api.deps import get_session

plan_router = APIRouter(prefix="/admin/plans", tags=["Plans"])
dashboard_router = APIRouter(prefix="/admin/dashboard", tags=["Dashboard"])


@plan_router.get("", response_model=list[PlanResponse])
async def list_plans(session: AsyncSession = Depends(get_session)):
    """List all available plans."""
    result = await session.execute(select(Plan).where(Plan.active == True))
    return result.scalars().all()


@dashboard_router.get("")
async def global_dashboard(session: AsyncSession = Depends(get_session)):
    """Platform-wide metrics dashboard."""

    # Total tenants by status
    status_counts = await session.execute(
        select(Tenant.status, func.count(Tenant.id))
        .group_by(Tenant.status)
    )
    tenants_by_status = {row[0]: row[1] for row in status_counts.fetchall()}

    # Total tenants
    total_tenants = sum(tenants_by_status.values())

    # Billing summary
    billing_result = await session.execute(
        select(
            func.count(BillingRecord.id),
            func.sum(BillingRecord.amount),
        ).where(BillingRecord.payment_status == "paid")
    )
    billing_row = billing_result.fetchone()

    return {
        "tenants": {
            "total": total_tenants,
            "by_status": tenants_by_status,
        },
        "billing": {
            "total_records": billing_row[0] or 0,
            "total_revenue": float(billing_row[1] or 0),
        },
    }
