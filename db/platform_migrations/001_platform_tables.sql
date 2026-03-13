-- ============================================================
-- DEM-005: Tabelas globais de plataforma (schema public)
-- Executar uma unica vez na inicializacao do sistema.
-- ============================================================

-- Tabela global de tenants
CREATE TABLE IF NOT EXISTS public.tenants (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT        NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{3,30}$'),
    name        TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'suspended', 'terminated')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabela global de auditoria de plataforma
CREATE TABLE IF NOT EXISTS public.platform_audit_log (
    id          BIGSERIAL   PRIMARY KEY,
    actor_id    TEXT        NOT NULL,
    actor_email TEXT,
    action      TEXT        NOT NULL,
    target_type TEXT,
    target_id   TEXT,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor  ON public.platform_audit_log (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON public.platform_audit_log (action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenants_slug     ON public.tenants (slug);

