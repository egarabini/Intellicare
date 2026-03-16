-- DEM-032: Clínico Gestão — professionals, professional_groups, group_members
-- Depende de DEM-031 (units table)

-- Profissionais de Saúde (pode já existir parcialmente via DEM-031)
CREATE TABLE IF NOT EXISTS professionals (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    council_type    TEXT        NOT NULL
                                CHECK (council_type IN ('CRM','COREN','CRO','CRP','CREFITO','other')),
    council_number  TEXT        NOT NULL,
    specialty       TEXT        NOT NULL,
    unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
    keycloak_id     TEXT        UNIQUE,
    phone           TEXT,
    email           TEXT,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Grupos de Profissionais
CREATE TABLE IF NOT EXISTS professional_groups (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    specialty       TEXT,
    unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
    description     TEXT,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Membros do grupo
CREATE TABLE IF NOT EXISTS group_members (
    group_id        INTEGER     NOT NULL REFERENCES professional_groups(id) ON DELETE CASCADE,
    professional_id INTEGER     NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, professional_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_professionals_unit   ON professionals (unit_id);
CREATE INDEX IF NOT EXISTS idx_professionals_status ON professionals (status);
CREATE INDEX IF NOT EXISTS idx_groups_unit          ON professional_groups (unit_id);
