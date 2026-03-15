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
    # DEM-031: Gestao Completa
    """
    CREATE TABLE IF NOT EXISTS professionals (
        id          SERIAL PRIMARY KEY,
        name        TEXT NOT NULL,
        specialty   TEXT,
        crm         TEXT,
        status      TEXT NOT NULL DEFAULT 'active'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS units (
        id              SERIAL PRIMARY KEY,
        name            TEXT        NOT NULL,
        type            TEXT        NOT NULL
                                    CHECK (type IN ('ubs','hospital','clinic','secretary','other')),
        cnes            TEXT,
        address         TEXT,
        city            TEXT,
        state           CHAR(2),
        phone           TEXT,
        email           TEXT,
        manager_user_id TEXT,
        status          TEXT        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active','inactive')),
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS unit_professionals (
        unit_id         INTEGER     NOT NULL REFERENCES units(id) ON DELETE CASCADE,
        professional_id INTEGER     NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
        role_in_unit    TEXT,
        workload_hours  INTEGER,
        allocated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (unit_id, professional_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tenant_users (
        id              SERIAL PRIMARY KEY,
        keycloak_id     TEXT        UNIQUE,
        email           TEXT        NOT NULL UNIQUE,
        name            TEXT        NOT NULL,
        role            TEXT        NOT NULL DEFAULT 'clinico'
                                    CHECK (role IN ('gestor','clinico','recepcionista')),
        unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
        status          TEXT        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active','inactive')),
        last_login_at   TIMESTAMPTZ,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_units_status ON units(status)",
    "CREATE INDEX IF NOT EXISTS idx_tenant_users_unit ON tenant_users(unit_id)",
    "CREATE INDEX IF NOT EXISTS idx_tenant_users_role ON tenant_users(role)",
]
