"""Migracoes SQL do modulo Florence (por tenant)."""
from __future__ import annotations

FLORENCE_MIGRATIONS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS clinical_notes (
        id           BIGSERIAL PRIMARY KEY,
        encounter_id UUID REFERENCES encounters(id) ON DELETE CASCADE,
        patient_id   UUID REFERENCES patients(id) ON DELETE CASCADE,
        author_id    TEXT NOT NULL,
        author_name  TEXT NOT NULL,
        note_type    TEXT NOT NULL DEFAULT 'FREE',
        soap_s       TEXT,
        soap_o       TEXT,
        soap_a       TEXT,
        soap_p       TEXT,
        free_text    TEXT,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_clinical_notes_encounter ON clinical_notes(encounter_id)",
    "CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient ON clinical_notes(patient_id)",
]
