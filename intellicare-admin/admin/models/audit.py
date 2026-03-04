from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from admin.db import Base

import os

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), nullable=False)
    actor_email = Column(String(255), nullable=False)
    actor_role = Column(String(100), nullable=False)

    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True))

    payload = Column(JSON)
    result = Column(String(50))
    error_message = Column(Text)

    ip = Column(String(45))
    user_agent = Column(Text)

    impersonated_as = Column(UUID(as_uuid=True))
    reason = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
