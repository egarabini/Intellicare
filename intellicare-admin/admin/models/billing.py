from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from admin.db import Base

import os

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class BillingRecord(Base):
    __tablename__ = "billing_records"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), ForeignKey(f"{SCHEMA}.tenants.tenant_id" if SCHEMA else "tenants.tenant_id"), nullable=False)
    
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    plan_name = Column(String(50))
    active_users = Column(Integer, default=0)
    sms_sent = Column(Integer, default=0)
    api_requests = Column(Integer, default=0)

    amount = Column(Numeric(10, 2))
    payment_status = Column(String(50), default="pending")  # pending, paid, overdue, cancelled
    
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

