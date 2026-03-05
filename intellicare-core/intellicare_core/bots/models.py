import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from intellicare_core.db.base import Base

class Bot(Base):
    __tablename__ = "bots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    code_version = Column(Integer, default=1)
    runtime = Column(String, default="sandbox")       # sandbox | subprocess
    status = Column(String, default="active")         # active | inactive
    run_as_user = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, default=30)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class BotSecret(Base):
    __tablename__ = "bot_secrets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    value_encrypted = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "bot_id", "name", name="uix_tenant_bot_secret_name"),
    )

class BotExecution(Base):
    __tablename__ = "bot_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String, nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), nullable=True)
    input_resource_type = Column(String, nullable=True)
    input_resource_id = Column(String, nullable=True)
    interaction = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    log_output = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
