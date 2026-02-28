"""GlobalAuditLog ORM model — schema 'platform'."""

import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from admin.models.tenant import Base


class GlobalAuditLog(Base):
    """Immutable audit log for all administrative actions across the platform."""

    __tablename__ = "audit_global"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String(255), nullable=False)  # "admin:uuid" or "support:uuid"
    action = Column(String(100), nullable=False, index=True)  # "tenant.created", "impersonation.started"
    resource_type = Column(String(100))  # "tenant", "plan", "module"
    resource_id = Column(String(255))
    target_tenant_id = Column(String(100), index=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by={self.actor_id} at={self.created_at}>"
