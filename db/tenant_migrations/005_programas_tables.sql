-- ============================================================
-- DEM-014: Programas de Saude
-- Tenant schema: tenant_{slug}
-- ============================================================

CREATE TABLE IF NOT EXISTS health_programs (
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    description  TEXT,
    target_count INTEGER NOT NULL DEFAULT 0,
    active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by   VARCHAR(100),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS program_enrollments (
    id          BIGSERIAL PRIMARY KEY,
    program_id  BIGINT NOT NULL REFERENCES health_programs(id) ON DELETE CASCADE,
    patient_id  UUID   NOT NULL REFERENCES patients(id)        ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enrolled_by VARCHAR(100),
    status      VARCHAR(20) NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active','discharged','suspended')),
    notes       TEXT,
    CONSTRAINT uq_enrollment UNIQUE (program_id, patient_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_program ON program_enrollments(program_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_patient ON program_enrollments(patient_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status  ON program_enrollments(status);
