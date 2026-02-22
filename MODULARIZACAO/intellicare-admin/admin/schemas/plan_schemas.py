"""Pydantic schemas for plan endpoints."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class PlanResponse(BaseModel):
    """Plan info response."""
    id: UUID
    name: str
    display_name: str
    max_users: int
    max_sms_month: int
    price_monthly: float
    modules_included: list[str] = []
    active: bool

    model_config = {"from_attributes": True}
