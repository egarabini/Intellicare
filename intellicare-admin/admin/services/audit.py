from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from admin.models.audit import AuditLog

class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        actor_id: UUID,
        actor_email: str,
        actor_role: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        payload: Optional[dict] = None,
        result: str = "success",
        error_message: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        impersonated_as: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> AuditLog:
        """
        Registra uma ação administrativa na trilha de auditoria.
        """
        log_entry = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload,
            result=result,
            error_message=error_message,
            ip=ip,
            user_agent=user_agent,
            impersonated_as=impersonated_as,
            reason=reason
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

    async def list_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        target_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        """
        Recupera os registros de auditoria com filtros opcionais.
        """
        stmt = select(AuditLog)
        
        if target_id:
            stmt = stmt.where(AuditLog.target_id == target_id)
        if actor_id:
             stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action:
             stmt = stmt.where(AuditLog.action == action)
             
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
