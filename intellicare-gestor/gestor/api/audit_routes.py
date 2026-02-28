"""Rotas de auditoria — 1 endpoint."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db
from gestor.models.audit import LocalAuditLog
from gestor.services.audit_service import AuditService

router = APIRouter()


class AuditLogResponse:
    pass


from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: dict
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


def _audit_service(session: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(session)


@router.get("/audit", response_model=list[AuditEntryResponse])
async def list_audit(
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    svc: AuditService = Depends(_audit_service),
):
    return await svc.list_logs(
        user_id=user_id,
        action=action,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
