"""Financeiro Router — endpoints REST do modulo financeiro."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import (
    BillingReport, ContractCreate, ContractResponse,
    InvoiceResponse, PlanCreate, PlanResponse,
)
from .service import FinanceiroService

router = APIRouter(tags=["financeiro"])
_svc = FinanceiroService()
AdminOnly = Annotated[TenantContext, Depends(require_role("PLATFORM_ADMIN"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "financeiro", "version": "1.0.0"}


# ---- Plans ----

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(actor: AdminOnly) -> list[dict]:
    return await _svc.list_plans()


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(payload: PlanCreate, actor: AdminOnly) -> dict:
    return await _svc.create_plan(payload, actor)


# ---- Contracts ----

@router.post("/contracts", response_model=ContractResponse, status_code=201)
async def create_contract(payload: ContractCreate, actor: AdminOnly) -> dict:
    try:
        return await _svc.create_contract(payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---- Invoices ----

@router.get("/contracts/{contract_id}/invoices", response_model=list[InvoiceResponse])
async def list_invoices(contract_id: UUID, actor: AdminOnly) -> list[dict]:
    return await _svc.list_invoices(contract_id)


@router.patch("/invoices/{invoice_id}/pay", response_model=InvoiceResponse)
async def mark_paid(invoice_id: UUID, actor: AdminOnly) -> dict:
    try:
        return await _svc.mark_paid(invoice_id, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---- Reports ----

@router.get("/reports/billing", response_model=BillingReport)
async def billing_report(
    actor: AdminOnly,
    year:  int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> dict:
    return await _svc.billing_report(year, month)
