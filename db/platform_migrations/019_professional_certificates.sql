-- DEM-080: Tabela de certificados digitais por profissional (tenant-scoped)
-- Aplica-se a cada schema de tenant

CREATE TABLE IF NOT EXISTS professional_certificates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professional_id INTEGER NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    pfx_encrypted   BYTEA NOT NULL,
    password_hash   TEXT NOT NULL,
    subject_name    TEXT,
    valid_until     DATE,
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_professional_certificate UNIQUE (professional_id)
);
