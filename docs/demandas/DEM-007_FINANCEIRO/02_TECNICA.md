---
dem: DEM-007
titulo: Módulo Financeiro — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-007 · 02 — Especificação Técnica

## Estrutura

```
modules/
└── financeiro/
    ├── __init__.py
    ├── main.py          # class Module(BaseModule)
    ├── router.py        # APIRouter
    ├── schemas.py       # Pydantic models
    ├── service.py       # FinanceiroService
    └── scheduler.py    # Job de inadimplência (APScheduler)

db/
└── platform_migrations/
    └── 002_financeiro_tables.sql
```

---

## BLOCO 1 — `db/platform_migrations/002_financeiro_tables.sql`

```sql
CREATE TABLE IF NOT EXISTS public.plans (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT        NOT NULL UNIQUE,
    price_brl      INTEGER     NOT NULL CHECK (price_brl >= 0),
    max_users      INTEGER     NOT NULL DEFAULT 50,
    max_storage_gb INTEGER     NOT NULL DEFAULT 10,
    cycle          TEXT        NOT NULL DEFAULT 'monthly'
                               CHECK (cycle IN ('monthly', 'annual')),
    active         BOOLEAN     NOT NULL DEFAULT true,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.contracts (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug  TEXT        NOT NULL REFERENCES public.tenants(slug) ON DELETE CASCADE,
    plan_id      UUID        NOT NULL REFERENCES public.plans(id),
    start_date   DATE        NOT NULL,
    end_date     DATE,
    status       TEXT        NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'cancelled')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.invoices (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id  UUID        NOT NULL REFERENCES public.contracts(id),
    tenant_slug  TEXT        NOT NULL,
    amount_brl   INTEGER     NOT NULL CHECK (amount_brl >= 0),
    due_date     DATE        NOT NULL,
    paid_at      TIMESTAMPTZ,
    status       TEXT        NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending', 'paid', 'overdue')),
    period_start DATE        NOT NULL,
    period_end   DATE        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_invoices_tenant  ON public.invoices (tenant_slug, due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_status  ON public.invoices (status, due_date);
CREATE INDEX IF NOT EXISTS idx_contracts_tenant ON public.contracts (tenant_slug);
```

---

## BLOCO 2 — `modules/financeiro/schemas.py`

```python
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
```

---

## BLOCO 3 — `modules/financeiro/service.py`

```python
"""FinanceiroService — lógica de negócio do módulo financeiro."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from uuid import UUID

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine
from .schemas import ContractCreate, PlanCreate

logger = logging.getLogger("intellicare.financeiro.service")


class FinanceiroService:

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    async def create_plan(self, payload: PlanCreate, actor: TenantContext) -> dict:
        async with get_engine().begin() as conn:
            row = (await conn.execute(
                text("""
                    INSERT INTO public.plans (name, price_brl, max_users, max_storage_gb, cycle)
                    VALUES (:name, :price_brl, :max_users, :max_storage_gb, :cycle)
                    RETURNING *
                """),
                payload.model_dump(),
            )).mappings().first()
        return dict(row)  # type: ignore[arg-type]

    async def list_plans(self) -> list[dict]:
        async with get_engine().connect() as conn:
            rows = (await conn.execute(
                text("SELECT * FROM public.plans WHERE active = true ORDER BY price_brl")
            )).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Contracts
    # ------------------------------------------------------------------

    async def create_contract(self, payload: ContractCreate, actor: TenantContext) -> dict:
        """Cria contrato e gera a primeira fatura."""
        async with get_engine().begin() as conn:
            # Buscar plan para obter preço
            plan = (await conn.execute(
                text("SELECT * FROM public.plans WHERE id = :plan_id AND active = true"),
                {"plan_id": str(payload.plan_id)},
            )).mappings().first()
            if not plan:
                raise LookupError(f"Plano {payload.plan_id} não encontrado ou inativo")

            # Criar contrato
            contract = (await conn.execute(
                text("""
                    INSERT INTO public.contracts (tenant_slug, plan_id, start_date)
                    VALUES (:tenant_slug, :plan_id, :start_date)
                    RETURNING *
                """),
                {
                    "tenant_slug": payload.tenant_slug,
                    "plan_id":     str(payload.plan_id),
                    "start_date":  payload.start_date,
                },
            )).mappings().first()

            # Gerar primeira fatura
            period_end = payload.start_date + relativedelta(months=1) - timedelta(days=1)
            due_date   = payload.start_date + timedelta(days=30)

            await conn.execute(
                text("""
                    INSERT INTO public.invoices
                        (contract_id, tenant_slug, amount_brl, due_date, period_start, period_end)
                    VALUES
                        (:contract_id, :tenant_slug, :amount_brl, :due_date, :period_start, :period_end)
                """),
                {
                    "contract_id":  str(contract["id"]),
                    "tenant_slug":  payload.tenant_slug,
                    "amount_brl":   plan["price_brl"],
                    "due_date":     due_date,
                    "period_start": payload.start_date,
                    "period_end":   period_end,
                },
            )

        logger.info("Contrato criado para tenant=%s plan=%s", payload.tenant_slug, payload.plan_id)
        return dict(contract)  # type: ignore[arg-type]

    async def list_invoices(self, contract_id: UUID) -> list[dict]:
        async with get_engine().connect() as conn:
            rows = (await conn.execute(
                text("""
                    SELECT * FROM public.invoices
                    WHERE contract_id = :cid
                    ORDER BY period_start DESC
                """),
                {"cid": str(contract_id)},
            )).mappings().all()
        return [dict(r) for r in rows]

    async def mark_paid(self, invoice_id: UUID, actor: TenantContext) -> dict:
        async with get_engine().begin() as conn:
            row = (await conn.execute(
                text("""
                    UPDATE public.invoices
                    SET status = 'paid', paid_at = now()
                    WHERE id = :id AND status != 'paid'
                    RETURNING *
                """),
                {"id": str(invoice_id)},
            )).mappings().first()
            if not row:
                raise LookupError(f"Fatura {invoice_id} não encontrada ou já paga")
        return dict(row)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def billing_report(self, year: int, month: int) -> dict:
        async with get_engine().connect() as conn:
            row = (await conn.execute(
                text("""
                    SELECT
                        COUNT(*)                                         AS invoice_count,
                        COALESCE(SUM(amount_brl), 0)                    AS total_invoiced_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'paid'),    0) AS total_paid_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'pending'), 0) AS total_pending_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'overdue'), 0) AS total_overdue_brl
                    FROM public.invoices
                    WHERE EXTRACT(YEAR  FROM period_start) = :year
                      AND EXTRACT(MONTH FROM period_start) = :month
                """),
                {"year": year, "month": month},
            )).mappings().first()
        return {**dict(row), "year": year, "month": month}  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Job de inadimplência
    # ------------------------------------------------------------------

    async def mark_overdue_and_suspend(self) -> int:
        """
        Marca faturas vencidas como 'overdue' e suspende tenants com
        fatura overdue há mais de 30 dias.
        Retorna o número de tenants suspensos.
        """
        async with get_engine().begin() as conn:
            # 1. Marcar como overdue
            await conn.execute(text("""
                UPDATE public.invoices
                SET status = 'overdue'
                WHERE status = 'pending'
                  AND due_date < CURRENT_DATE
            """))

            # 2. Identificar tenants com overdue > 30 dias
            rows = (await conn.execute(text("""
                SELECT DISTINCT tenant_slug
                FROM public.invoices
                WHERE status = 'overdue'
                  AND due_date < CURRENT_DATE - INTERVAL '30 days'
            """))).fetchall()

            suspended = 0
            for row in rows:
                slug = row[0]
                await conn.execute(
                    text("UPDATE public.tenants SET status='suspended', updated_at=now() WHERE slug=:slug AND status='active'"),
                    {"slug": slug},
                )
                suspended += 1
                logger.warning("Tenant '%s' suspenso por inadimplência", slug)

        return suspended
```

---

## BLOCO 4 — `modules/financeiro/router.py`

```python
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

router = APIRouter(prefix="/financeiro", tags=["financeiro"])
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
```

---

## BLOCO 5 — `modules/financeiro/scheduler.py`

```python
"""
scheduler.py — Job diário de verificação de inadimplência.
Integrado via APScheduler no startup do intellicare-service.
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .service import FinanceiroService

logger = logging.getLogger("intellicare.financeiro.scheduler")


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    svc = FinanceiroService()

    @scheduler.scheduled_job(CronTrigger(hour=3, minute=0))  # 03:00 todo dia
    async def check_overdue():
        logger.info("Iniciando verificação de inadimplência...")
        suspended = await svc.mark_overdue_and_suspend()
        logger.info("Verificação concluída. Tenants suspensos: %d", suspended)

    scheduler.start()
    logger.info("Scheduler financeiro iniciado (job diário às 03:00)")
    return scheduler
```

Registrar no startup da aplicação (`intellicare_core/main.py`):

```python
# Em lifespan ou on_startup:
from modules.financeiro.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()
```

---

## BLOCO 6 — `modules/financeiro/main.py`

```python
from fastapi import APIRouter
from intellicare_core.contracts.base import BaseModule, HealthResponse
from .router import router as fin_router


class Module(BaseModule):
    @property
    def name(self) -> str:
        return "financeiro"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return fin_router

    async def health(self) -> HealthResponse:
        return HealthResponse(status="healthy", module=self.name, version=self.version)
```

---

## BLOCO 7 — `tests/financeiro/test_financeiro_service.py`

```python
"""Testes unitários do FinanceiroService."""
import pytest
from modules.financeiro.schemas import PlanCreate, ContractCreate
from datetime import date


def test_plan_price_negativo():
    with pytest.raises(ValueError, match="price_brl"):
        PlanCreate(name="Plano X", price_brl=-100)


def test_plan_cycle_invalido():
    with pytest.raises(ValueError):
        PlanCreate(name="Plano X", price_brl=0, cycle="weekly")  # type: ignore


def test_plan_criacao_valida():
    p = PlanCreate(name="Básico", price_brl=9900, max_users=10, cycle="monthly")
    assert p.price_brl == 9900
    assert p.cycle == "monthly"


def test_contract_create_schema():
    import uuid
    c = ContractCreate(
        tenant_slug="clinica_sp",
        plan_id=uuid.uuid4(),
        start_date=date.today(),
    )
    assert c.tenant_slug == "clinica_sp"
```

---

## BLOCO 8 — Commit

```bash
git add modules/financeiro/ \
        db/platform_migrations/002_financeiro_tables.sql \
        tests/financeiro/ \
        docs/demandas/DEM-007_FINANCEIRO/

git commit -m "DEM-007: Módulo Financeiro - planos, contratos, faturas, job inadimplência"
git push origin main
```

---

## Critérios de Aceite (técnicos)

| # | Critério | Verificação |
|---|---|---|
| AC-1 | POST `/financeiro/plans` cria plano | `GET /financeiro/plans` → aparece na lista |
| AC-2 | POST `/financeiro/contracts` gera contrato + fatura | `GET /financeiro/contracts/{id}/invoices` → 1 fatura `pending` |
| AC-3 | PATCH `/financeiro/invoices/{id}/pay` → status `paid` | `paid_at` preenchido |
| AC-4 | Job `mark_overdue_and_suspend` marca faturas vencidas | Fatura com `due_date = ontem` → status `overdue` |
| AC-5 | Tenant com overdue > 30d → status `suspended` | `SELECT status FROM public.tenants` |
| AC-6 | GET `/financeiro/reports/billing` → totais corretos | Soma manual conferida |
| AC-7 | Rota sem token → 401; token CLINICO → 403 | curl sem header |
| AC-8 | Testes unitários passam | `pytest tests/financeiro/ -v` |
