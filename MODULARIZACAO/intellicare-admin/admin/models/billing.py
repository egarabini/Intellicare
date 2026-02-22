"""BillingRecord ORM model — schema 'platform'."""

import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from admin.models.tenant import Base


class BillingRecord(Base):
    """Monthly billing record per tenant."""

    __tablename__ = "billing_records"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        String(100),
        ForeignKey("platform.tenants.tenant_id"),
        nullable=False,
        index=True,
    )
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    plan_name = Column(String(50))

    # Usage
    active_users = Column(Integer, default=0)
    sms_sent = Column(Integer, default=0)
    api_requests = Column(Integer, default=0)

    # Financial
    amount = Column(Numeric(10, 2), default=0)
    payment_status = Column(String(20), default="pending")  # pending, paid, overdue, grace
    paid_at = Column(DateTime)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship
    tenant = relationship("Tenant", back_populates="billing_records")

    def __repr__(self) -> str:
        return f"<BillingRecord {self.tenant_id} {self.period_start:%Y-%m} status={self.payment_status}>"
