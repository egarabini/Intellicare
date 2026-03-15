-- ============================================================
-- DEM-030: Administrativo completo (schema public)
-- Depende de 001_platform_tables.sql e 002_financeiro_tables.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS public.servers (
    id          SERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    type        TEXT        NOT NULL CHECK (type IN ('vps', 'dedicated', 'cloud')),
    provider    TEXT        NOT NULL,
    region      TEXT        NOT NULL,
    hostname    TEXT,
    vcpu        INTEGER     NOT NULL CHECK (vcpu > 0),
    ram_gb      INTEGER     NOT NULL CHECK (ram_gb > 0),
    disk_gb     INTEGER     NOT NULL CHECK (disk_gb > 0),
    cost_brl    INTEGER     NOT NULL DEFAULT 0 CHECK (cost_brl >= 0),
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'maintenance')),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.platform_modules (
    id          SERIAL PRIMARY KEY,
    slug        TEXT        NOT NULL UNIQUE,
    name        TEXT        NOT NULL,
    description TEXT,
    version     TEXT        NOT NULL DEFAULT '1.0.0',
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'dev')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.tenant_modules (
    tenant_slug TEXT        NOT NULL REFERENCES public.tenants(slug) ON DELETE CASCADE,
    module_slug TEXT        NOT NULL REFERENCES public.platform_modules(slug) ON DELETE CASCADE,
    enabled     BOOLEAN     NOT NULL DEFAULT true,
    enabled_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_slug, module_slug)
);

CREATE TABLE IF NOT EXISTS public.expenses (
    id           SERIAL PRIMARY KEY,
    category     TEXT        NOT NULL
                             CHECK (category IN ('infrastructure', 'license', 'personnel', 'other')),
    description  TEXT        NOT NULL,
    amount_brl   INTEGER     NOT NULL CHECK (amount_brl > 0),
    expense_date DATE        NOT NULL,
    tenant_slug  TEXT        REFERENCES public.tenants(slug) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.admin_users (
    id            SERIAL PRIMARY KEY,
    keycloak_id   TEXT UNIQUE,
    email         TEXT        NOT NULL UNIQUE,
    name          TEXT        NOT NULL,
    role          TEXT        NOT NULL DEFAULT 'coordenador'
                              CHECK (role IN ('admin', 'financ', 'coordenador')),
    status        TEXT        NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active', 'inactive')),
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_servers_status ON public.servers (status);
CREATE INDEX IF NOT EXISTS idx_platform_modules_status ON public.platform_modules (status);
CREATE INDEX IF NOT EXISTS idx_tenant_modules_tenant ON public.tenant_modules (tenant_slug);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON public.expenses (expense_date DESC);
CREATE INDEX IF NOT EXISTS idx_admin_users_status ON public.admin_users (status);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'invoices'
          AND constraint_name = 'invoices_status_check'
    ) THEN
        ALTER TABLE public.invoices DROP CONSTRAINT invoices_status_check;
    END IF;
END $$;

ALTER TABLE public.invoices
    ADD CONSTRAINT invoices_status_check
    CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled'));

INSERT INTO public.platform_modules (slug, name, description, version, status) VALUES
    ('admin', 'Administrativo', 'Gestao da plataforma', '3.0.0', 'active'),
    ('gestor', 'Gestao', 'Gestao de unidades e usuarios', '3.0.0', 'active'),
    ('cuidado', 'Clinico', 'Prontuario e atendimento', '3.0.0', 'active'),
    ('florence', 'Florence AI', 'Assistente IA de saude', '1.0.0', 'dev'),
    ('oswaldo', 'Oswaldo BI', 'Business Intelligence de saude', '1.0.0', 'dev')
ON CONFLICT (slug) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    version = EXCLUDED.version;
