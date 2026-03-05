import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from gestor.models.base import Base

class LocalAuditLog(Base):
    __tablename__ = "audit_local"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # "user.created", "role.updated"
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
