CREATE TABLE IF NOT EXISTS clinical_notes (
    id          BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    patient_id  BIGINT NOT NULL,
    author_id   UUID NOT NULL,              -- sub do Keycloak
    author_name TEXT NOT NULL,
    note_type   TEXT NOT NULL DEFAULT 'FREE', -- FREE | SOAP
    -- campos SOAP (todos opcionais)
    soap_s      TEXT,                        -- Subjetivo
    soap_o      TEXT,                        -- Objetivo
    soap_a      TEXT,                        -- Avaliação
    soap_p      TEXT,                        -- Plano
    -- campo livre (sempre presente como fallback)
    free_text   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clinical_notes_encounter ON clinical_notes(encounter_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient   ON clinical_notes(patient_id);
