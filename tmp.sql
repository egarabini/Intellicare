SET search_path TO tenant_dev, public;  
CREATE TABLE IF NOT EXISTS prescriptions (
    id              BIGSERIAL PRIMARY KEY,
    encounter_id    UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    patient_id      UUID NOT NULL,
    author_id       UUID NOT NULL,
    author_name     TEXT NOT NULL,
    cid10_code      TEXT,                    
    cid10_desc      TEXT,                    
    items           JSONB NOT NULL DEFAULT '[]',
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'DRAFT',  
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_encounter ON prescriptions(encounter_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient   ON prescriptions(patient_id);
