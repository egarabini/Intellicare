"""Audit API routes — /admin/audit"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.audit import GlobalAuditLog
from admin.api.deps import get_db as get_session

router = APIRouter(prefix="/admin/audit", tags=["Audit"])


@router.get("")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, description="Filter by action type e.g. tenant.created"),
    actor_id: Optional[str] = Query(None, description="Filter by actor"),
    target_tenant_id: Optional[str] = Query(None, description="Filter by target tenant"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Query the global audit log with filters."""
    query = select(GlobalAuditLog)
    count_query = select(func.count(GlobalAuditLog.id))

    # Apply filters
    if action:
        query = query.where(GlobalAuditLog.action == action)
        count_query = count_query.where(GlobalAuditLog.action == action)

    if actor_id:
        query = query.where(GlobalAuditLog.actor_id.ilike(f"%{actor_id}%"))
        count_query = count_query.where(GlobalAuditLog.actor_id.ilike(f"%{actor_id}%"))

    if target_tenant_id:
        query = query.where(GlobalAuditLog.target_tenant_id == target_tenant_id)
        count_query = count_query.where(GlobalAuditLog.target_tenant_id == target_tenant_id)

    if date_from:
        query = query.where(GlobalAuditLog.created_at >= date_from)
        count_query = count_query.where(GlobalAuditLog.created_at >= date_from)

    if date_to:
        query = query.where(GlobalAuditLog.created_at <= date_to)
        count_query = count_query.where(GlobalAuditLog.created_at <= date_to)

    # Count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(GlobalAuditLog.created_at.desc())
    result = await session.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "actor_id": log.actor_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "target_tenant_id": log.target_tenant_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/actions")
async def list_audit_actions(
    session: AsyncSession = Depends(get_session),
):
    """List all distinct action types in the audit log (for filter dropdowns)."""
    result = await session.execute(
        select(GlobalAuditLog.action, func.count(GlobalAuditLog.id))
        .group_by(GlobalAuditLog.action)
        .order_by(func.count(GlobalAuditLog.id).desc())
    )
    return [
        {"action": row[0], "count": row[1]}
        for row in result.fetchall()
    ]
