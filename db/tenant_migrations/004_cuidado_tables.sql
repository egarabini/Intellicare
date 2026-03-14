-- DEM-013: Cuidado Backend — tabelas clínicas (por tenant schema)

CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    cpf TEXT UNIQUE,
    birth_date DATE,
    sex CHAR(1) CHECK (sex IN ('M','F','O')),
    phone TEXT, email TEXT, address TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    clinician_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
    chief_complaint TEXT,
    priority TEXT NOT NULL DEFAULT 'normal'
              CHECK (priority IN ('emergency','urgent','normal','low')),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS encounter_notes (
    id BIGSERIAL PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    clinician_id TEXT NOT NULL,
    subjective TEXT, objective TEXT, assessment TEXT, plan TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters (patient_id, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_encounter    ON encounter_notes (encounter_id, created_at);
CREATE INDEX IF NOT EXISTS idx_patients_name      ON patients USING gin (to_tsvector('portuguese', full_name));

