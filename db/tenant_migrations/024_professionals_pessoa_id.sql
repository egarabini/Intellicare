-- db/tenant_migrations/024_professionals_pessoa_id.sql
ALTER TABLE {schema}.professionals
  ADD COLUMN IF NOT EXISTS pessoa_id UUID;

-- Índice para lookup por pessoa_id (futuro: busca cross-tenant)
CREATE INDEX IF NOT EXISTS idx_professionals_pessoa_id
    ON {schema}.professionals(pessoa_id)
    WHERE pessoa_id IS NOT NULL;
