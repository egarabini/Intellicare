"""Model ORM — TenantSetting."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, String, Text
from sqlalchemy.orm import mapped_column

from gestor.models.base import Base


class TenantSetting(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)   # "branding", "comunicacao", "modulos"
    key = Column(String(255), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string", nullable=False)  # string|number|boolean|json
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )
    updated_by = Column(UUID(as_uuid=True), nullable=True)
