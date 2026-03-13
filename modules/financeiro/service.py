"""FinanceiroService — logica de negocio do modulo financeiro."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from uuid import UUID

from dateutil.relativedelta import relativedelta
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
            # Buscar plan para obter preco
            plan = (await conn.execute(
                text("SELECT * FROM public.plans WHERE id = :plan_id AND active = true"),
                {"plan_id": str(payload.plan_id)},
            )).mappings().first()
            if not plan:
                raise LookupError(f"Plano {payload.plan_id} nao encontrado ou inativo")

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
                    "contract_id":  str(contract["id"]),  # type: ignore[index]
                    "tenant_slug":  payload.tenant_slug,
                    "amount_brl":   plan["price_brl"],  # type: ignore[index]
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
                raise LookupError(f"Fatura {invoice_id} nao encontrada ou ja paga")
        return dict(row)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def billing_report(self, year: int, month: int) -> dict:
        async with get_engine().connect() as conn:
            row = (await conn.execute(
                text("""
                    SELECT
                        COUNT(*)                                                        AS invoice_count,
                        COALESCE(SUM(amount_brl), 0)                                   AS total_invoiced_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'paid'),    0)  AS total_paid_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'pending'), 0)  AS total_pending_brl,
                        COALESCE(SUM(amount_brl) FILTER (WHERE status = 'overdue'), 0)  AS total_overdue_brl
                    FROM public.invoices
                    WHERE EXTRACT(YEAR  FROM period_start) = :year
                      AND EXTRACT(MONTH FROM period_start) = :month
                """),
                {"year": year, "month": month},
            )).mappings().first()
        return {**dict(row), "year": year, "month": month}  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Job de inadimplencia
    # ------------------------------------------------------------------

    async def mark_overdue_and_suspend(self) -> int:
        """
        Marca faturas vencidas como 'overdue' e suspende tenants com
        fatura overdue ha mais de 30 dias.
        Retorna o numero de tenants suspensos.
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
                result = await conn.execute(
                    text("""
                        UPDATE public.tenants
                        SET status = 'suspended', updated_at = now()
                        WHERE slug = :slug AND status = 'active'
                    """),
                    {"slug": slug},
                )
                if result.rowcount > 0:
                    suspended += 1
                    logger.warning("Tenant '%s' suspenso por inadimplencia", slug)

        return suspended

