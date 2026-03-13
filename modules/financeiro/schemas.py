"""Pydantic models (request/response) do modulo financeiro."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


# ---- Plans ----

class PlanCreate(BaseModel):
    name: str
    price_brl: int          # centavos
    max_users: int = 50
    max_storage_gb: int = 10
    cycle: Literal["monthly", "annual"] = "monthly"

    @field_validator("price_brl")
    @classmethod
    def price_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("price_brl deve ser >= 0")
        return v


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    price_brl: int
    max_users: int
    max_storage_gb: int
    cycle: str
    active: bool
    created_at: datetime


# ---- Contracts ----

class ContractCreate(BaseModel):
    tenant_slug: str
    plan_id: UUID
    start_date: date


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_slug: str
    plan_id: UUID
    start_date: date
    end_date: Optional[date]
    status: str
    created_at: datetime


# ---- Invoices ----

class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    contract_id: UUID
    tenant_slug: str
    amount_brl: int
    due_date: date
    paid_at: Optional[datetime]
    status: str
    period_start: date
    period_end: date
    created_at: datetime


# ---- Reports ----

class BillingReport(BaseModel):
    year: int
    month: int
    total_invoiced_brl: int
    total_paid_brl: int
    total_pending_brl: int
    total_overdue_brl: int
    invoice_count: int

