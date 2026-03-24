-- db/tenant_migrations/022_paciente_pessoa_id.sql
ALTER TABLE {schema}.patients
ADD COLUMN IF NOT EXISTS pessoa_id UUID;

-- Índice para lookup por pessoa_id (futuro: busca cross-tenant)
CREATE INDEX IF NOT EXISTS idx_patients_pessoa_id
    ON {schema}.patients(pessoa_id)
    WHERE pessoa_id IS NOT NULL;
