"""Plan ORM model — schema 'platform'."""

import uuid
import os
from sqlalchemy import Column, String, Boolean, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from admin.models.tenant import Base

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class Plan(Base):
    """Subscription plans available on the platform."""

    __tablename__ = "plan"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  # trial, basico, etc.
    display_name = Column(String(100), nullable=False)
    max_users = Column(Integer, default=5)
    max_sms_month = Column(Integer, default=100)
    price_monthly = Column(Numeric(10, 2), default=0)
    modules_included = Column(JSON, default=list)  # ["zilda", "florence", ...]
    active = Column(Boolean, default=True)

    # Relationships
    tenants = relationship("Tenant", back_populates="plan", lazy="noload")

    def __repr__(self) -> str:
        return f"<Plan {self.name} users={self.max_users}>"
