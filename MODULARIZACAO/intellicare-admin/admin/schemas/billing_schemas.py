"""Pydantic schemas for billing endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class BillingResponse(BaseModel):
    """Billing record response."""
    id: UUID
    tenant_id: str
    period_start: datetime
    period_end: datetime
    plan_name: Optional[str] = None
    active_users: int = 0
    sms_sent: int = 0
    api_requests: int = 0
    amount: float = 0
    payment_status: str = "pending"
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
