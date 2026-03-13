"""Testes unitarios do FinanceiroService."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from modules.financeiro.schemas import (
    BillingReport,
    ContractCreate,
    ContractResponse,
    InvoiceResponse,
    PlanCreate,
    PlanResponse,
)


# ------------------------------------------------------------------
# PlanCreate validation
# ------------------------------------------------------------------

def test_plan_price_negativo():
    with pytest.raises(ValueError, match="price_brl"):
        PlanCreate(name="Plano X", price_brl=-100)


def test_plan_cycle_invalido():
    with pytest.raises(ValueError):
        PlanCreate(name="Plano X", price_brl=0, cycle="weekly")  # type: ignore[arg-type]


def test_plan_criacao_valida():
    p = PlanCreate(name="Basico", price_brl=9900, max_users=10, cycle="monthly")
    assert p.price_brl == 9900
    assert p.cycle == "monthly"
    assert p.max_storage_gb == 10


def test_plan_defaults():
    p = PlanCreate(name="Default", price_brl=0)
    assert p.max_users == 50
    assert p.max_storage_gb == 10
    assert p.cycle == "monthly"


def test_plan_price_zero_valido():
    p = PlanCreate(name="Free", price_brl=0)
    assert p.price_brl == 0


# ------------------------------------------------------------------
# ContractCreate validation
# ------------------------------------------------------------------

def test_contract_create_schema():
    c = ContractCreate(
        tenant_slug="clinica_sp",
        plan_id=uuid.uuid4(),
        start_date=date.today(),
    )
    assert c.tenant_slug == "clinica_sp"
    assert isinstance(c.start_date, date)


def test_contract_create_with_specific_date():
    plan_id = uuid.uuid4()
    c = ContractCreate(
        tenant_slug="hospital_rj",
        plan_id=plan_id,
        start_date=date(2026, 1, 15),
    )
    assert c.start_date == date(2026, 1, 15)
    assert c.plan_id == plan_id


# ------------------------------------------------------------------
# Response models
# ------------------------------------------------------------------

def test_billing_report_schema():
    r = BillingReport(
        year=2026,
        month=3,
        total_invoiced_brl=100000,
        total_paid_brl=80000,
        total_pending_brl=15000,
        total_overdue_brl=5000,
        invoice_count=10,
    )
    assert r.total_invoiced_brl == 100000
    assert r.invoice_count == 10


def test_plan_cycle_annual():
    p = PlanCreate(name="Enterprise", price_brl=120000, cycle="annual")
    assert p.cycle == "annual"

