-- ============================================================
-- DEM-007: Tabelas do modulo financeiro (schema public)
-- Depende de 001_platform_tables.sql (public.tenants)
-- ============================================================

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

