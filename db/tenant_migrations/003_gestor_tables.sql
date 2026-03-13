-- DEM-011: Gestor Backend — tabelas do tenant
-- Executada dentro do schema tenant_{slug}

CREATE TABLE IF NOT EXISTS unit_profile (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    address     TEXT,
    city        TEXT,
    state       CHAR(2),
    unit_type   TEXT        DEFAULT 'clinic'
                            CHECK (unit_type IN ('ubs','clinic','hospital','specialty')),
    phone       TEXT,
    email       TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS slm_query_log (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    query_text  TEXT        NOT NULL,
    latency_ms  INTEGER,
    chunk_count INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_slm_log_created ON slm_query_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_slm_log_user    ON slm_query_log (user_id, created_at DESC);
