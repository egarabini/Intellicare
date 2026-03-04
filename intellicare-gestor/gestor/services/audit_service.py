import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from gestor.models.audit import LocalAuditLog

class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> LocalAuditLog:
        """Registra uma nova ação no log unificado de auditoria local (append-only) do tenant."""
        audit_log = LocalAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log

    async def list_logs(self, skip: int = 0, limit: int = 100) -> List[LocalAuditLog]:
        result = await self.session.execute(
            select(LocalAuditLog).order_by(LocalAuditLog.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
