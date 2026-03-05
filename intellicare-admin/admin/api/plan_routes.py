"""Plan and Dashboard API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.plan import Plan
from admin.models.tenant import Tenant, TenantModule
from admin.models.billing import BillingRecord
from admin.models.tenant_gestor import TenantGestor
from admin.models.audit import GlobalAuditLog
from admin.schemas.plan_schemas import PlanResponse
from admin.api.deps import get_db as get_session, require_platform_admin

plan_router = APIRouter(prefix="/admin/plans", tags=["Plans"], dependencies=[Depends(require_platform_admin)])
dashboard_router = APIRouter(prefix="/admin/dashboard", tags=["Dashboard"], dependencies=[Depends(require_platform_admin)])

@plan_router.get("", response_model=list[PlanResponse])
async def list_plans(session: AsyncSession = Depends(get_session)):
    """List all available plans."""
    result = await session.execute(select(Plan).where(Plan.active == True))
    return result.scalars().all()

@dashboard_router.get("")
async def global_dashboard(session: AsyncSession = Depends(get_session)):
    """Platform-wide metrics dashboard."""

    # 1. Total tenants by status
    status_counts = await session.execute(
        select(Tenant.status, func.count(Tenant.id)).group_by(Tenant.status)
    )
    tenants_by_status = {row[0]: row[1] for row in status_counts.fetchall()}
    total_tenants = sum(tenants_by_status.values())

    # 2. Most used modules
    module_counts = await session.execute(
        select(TenantModule.module_name, func.count(TenantModule.id))
        .where(TenantModule.enabled == True)
        .group_by(TenantModule.module_name)
        .order_by(desc(func.count(TenantModule.id)))
        .limit(5)
    )
    modulos_mais_usados = [{"nome": row[0], "tenants_ativos": row[1]} for row in module_counts.fetchall()]

    # 3. Total Gestores
    gestores_result = await session.execute(select(func.count(TenantGestor.id)).where(TenantGestor.active == True))
    gestores_totais = gestores_result.scalar() or 0

    # 4. Latest Audit Activities
    audit_result = await session.execute(
        select(GlobalAuditLog)
        .order_by(GlobalAuditLog.created_at.desc())
        .limit(10)
    )
    ultimas_atividades = audit_result.scalars().all()

    # Serialize activities securely
    atividades_list = [
        {
            "id": str(log.id),
            "acao": log.action,
            "recurso": f"{log.resource_type}:{log.resource_id}" if log.resource_type else None,
            "operador": log.actor_id,
            "tenant_id": log.target_tenant_id,
            "data": log.created_at.isoformat() if log.created_at else None
        } for log in ultimas_atividades
    ]

    return {
        "totais": {
            "tenants": total_tenants,
            "ativos": tenants_by_status.get("active", 0) + tenants_by_status.get("provisioned", 0),
            "suspensos": tenants_by_status.get("suspended", 0),
            "trial": tenants_by_status.get("trial", 0),
        },
        "modulos_mais_usados": modulos_mais_usados,
        "gestores_totais": gestores_totais,
        "ultimas_atividades": atividades_list
    }
