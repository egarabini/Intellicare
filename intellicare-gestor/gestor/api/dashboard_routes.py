"""Rotas do dashboard do gestor — 1 endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db
from gestor.models.audit import LocalAuditLog
from gestor.models.role import Role
from gestor.models.sector import Sector
from gestor.models.user import TenantUser

router = APIRouter()


@router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_db)):
    """Dashboard com visão geral do tenant."""

    # Contagens
    total_users = (
        await session.execute(select(func.count()).select_from(TenantUser))
    ).scalar_one()

    active_users = (
        await session.execute(
            select(func.count()).where(TenantUser.active == True)
        )
    ).scalar_one()

    total_roles = (
        await session.execute(select(func.count()).select_from(Role))
    ).scalar_one()

    total_sectors = (
        await session.execute(
            select(func.count()).where(Sector.active == True)
        )
    ).scalar_one()

    # Últimas atividades (10 mais recentes)
    recent_logs_result = await session.execute(
        select(LocalAuditLog)
        .order_by(LocalAuditLog.created_at.desc())
        .limit(10)
    )
    recent_logs = recent_logs_result.scalars().all()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
        "roles": {"total": total_roles},
        "sectors": {"active": total_sectors},
        "recent_activity": [
            {
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "created_at": log.created_at,
            }
            for log in recent_logs
        ],
    }
