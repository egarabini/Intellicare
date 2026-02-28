"""AuditService — Log de auditoria append-only do tenant."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.audit import LocalAuditLog


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> LocalAuditLog:
        entry = LocalAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LocalAuditLog]:
        q = select(LocalAuditLog).order_by(LocalAuditLog.created_at.desc())

        if user_id:
            q = q.where(LocalAuditLog.user_id == user_id)
        if action:
            q = q.where(LocalAuditLog.action == action)
        if since:
            q = q.where(LocalAuditLog.created_at >= since)
        if until:
            q = q.where(LocalAuditLog.created_at <= until)

        q = q.limit(limit).offset(offset)
        result = await self._session.execute(q)
        return list(result.scalars().all())
