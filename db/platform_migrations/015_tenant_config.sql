-- ============================================================
-- DEM-065: Tabela tenant_config no schema platform (public).
-- Configurações avançadas por tenant: limites, features, etc.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.tenant_config (
    tenant_slug TEXT        NOT NULL REFERENCES public.tenants(slug) ON DELETE CASCADE,
    key         TEXT        NOT NULL,
    value       TEXT        NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_slug, key)
);

CREATE INDEX IF NOT EXISTS idx_tenant_config_slug
    ON public.tenant_config (tenant_slug);

-- Coluna suspended_at para controle de suspensão
ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS suspended_at  TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS suspended_by  TEXT,
    ADD COLUMN IF NOT EXISTS deleted_at    TIMESTAMPTZ;
