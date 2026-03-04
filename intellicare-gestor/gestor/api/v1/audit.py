from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from gestor.db import get_db
from gestor.services.audit_service import AuditService
from gestor.schemas.audit_schemas import LocalAuditLogResponse, AuditListResponse
from gestor.middleware import require_permission

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", response_model=AuditListResponse)
@require_permission("gestor.auditoria")
async def list_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    service = AuditService(db)
    logs = await service.list_logs(skip=skip, limit=limit)
    return AuditListResponse(logs=logs, total=len(logs))
