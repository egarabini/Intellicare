from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from admin.db import Base

import os

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class GlobalAuditLog(Base):
    __tablename__ = "global_audit_logs"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    target_tenant_id = Column(String(50))

    details = Column(JSON)
    ip_address = Column(String(45))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
