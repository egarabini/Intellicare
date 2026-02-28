"""Model ORM — LocalAuditLog (append-only)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, JSON, String

from gestor.models.base import Base


class LocalAuditLog(Base):
    __tablename__ = "audit_local"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)       # "user.created", "role.updated"
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
