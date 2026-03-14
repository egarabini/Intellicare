from __future__ import annotations

GESTOR_MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS patients (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        cpf CHAR(11) NOT NULL,
        birth_date DATE NOT NULL,
        email TEXT,
        phone TEXT,
        health_plan TEXT,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(cpf)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS patients_name_idx
        ON patients USING gin(to_tsvector('portuguese', name))
    """,
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        patient_id UUID NOT NULL REFERENCES patients(id),
        clinician_id UUID NOT NULL,
        scheduled_at TIMESTAMPTZ NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('consulta','retorno','exame')),
        status TEXT NOT NULL DEFAULT 'agendado'
            CHECK (status IN ('agendado','confirmado','realizado','cancelado')),
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS appt_clinician_date
        ON appointments(clinician_id, scheduled_at)
    """,
]
