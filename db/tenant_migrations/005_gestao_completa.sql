-- DEM-031: Gestao Completa — unidades, alocacao profissionais, usuarios tenant

-- Profissionais (caso nao exista — referenciado por unit_professionals)
CREATE TABLE IF NOT EXISTS professionals (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    council_type TEXT,
    council_number TEXT,
    specialty   TEXT,
    crm         TEXT,
    unit_id     INTEGER,
    keycloak_id TEXT UNIQUE,
    phone       TEXT,
    email       TEXT,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unidades de Saude
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
);

-- Alocacao de profissionais em unidades
CREATE TABLE IF NOT EXISTS unit_professionals (
    unit_id         INTEGER     NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    professional_id INTEGER     NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    role_in_unit    TEXT,
    workload_hours  INTEGER,
    allocated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (unit_id, professional_id)
);

-- Usuarios do Tenant
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
);

CREATE INDEX IF NOT EXISTS idx_units_status ON units(status);
CREATE INDEX IF NOT EXISTS idx_tenant_users_unit ON tenant_users(unit_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_role ON tenant_users(role);
