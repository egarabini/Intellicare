-- ============================================================
-- DEM-005: DDL executado dentro do schema do tenant ao provisiona-lo.
-- O TenantService.create_tenant() injeta search_path antes de rodar.
-- ============================================================

-- Tabela de usuarios local do tenant (espelho leve do Keycloak)
CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_id TEXT        NOT NULL UNIQUE,
    email       TEXT        NOT NULL,
    name        TEXT        NOT NULL,
    role        TEXT        NOT NULL CHECK (role IN ('TENANT_GESTOR','CLINICO','PACIENTE')),
    active      BOOLEAN     NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabela de base de conhecimento (RAG) — base vazia, populada pelo ingest pipeline
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          BIGSERIAL   PRIMARY KEY,
    title       TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    source_path TEXT,
    embedding   vector(768),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_embedding
    ON knowledge_base USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

