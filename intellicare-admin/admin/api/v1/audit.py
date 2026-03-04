from fastapi import APIRouter, Depends, Query
from typing import Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from admin.db import get_db
from admin.schemas.audit import AuditLogList
from admin.services.audit import AuditService
from admin.models.audit import AuditLog

router = APIRouter()

@router.get(
    "",
    response_model=AuditLogList,
)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    target_id: Optional[UUID] = Query(None),
    actor_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    # TODO: current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Lista registros de auditoria (apenas PLATFORM_ADMIN tem acesso total).
    """
    audit_service = AuditService(db)
    items = await audit_service.list_logs(
        skip=skip,
        limit=limit,
        target_id=target_id,
        actor_id=actor_id,
        action=action
    )
    
    # Contar total
    from sqlalchemy import func
    stmt_count = select(func.count(AuditLog.id))
    if target_id: stmt_count = stmt_count.where(AuditLog.target_id == target_id)
    if actor_id: stmt_count = stmt_count.where(AuditLog.actor_id == actor_id)
    if action: stmt_count = stmt_count.where(AuditLog.action == action)
    
    total = (await db.execute(stmt_count)).scalar_one()

    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit
    }
