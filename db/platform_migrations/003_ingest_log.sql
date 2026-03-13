-- Adicionado ao schema tenant_{slug} durante provisionamento

CREATE TABLE IF NOT EXISTS ingest_log (
    id              BIGSERIAL   PRIMARY KEY,
    source_path     TEXT        NOT NULL,
    chunk_count     INTEGER     NOT NULL DEFAULT 0,
    status          TEXT        NOT NULL DEFAULT 'ok' CHECK (status IN ('ok','error')),
    error_message   TEXT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingest_log_path ON ingest_log (source_path, ingested_at DESC);

-- Adicionar chunk_index à knowledge_base para upsert idempotente
ALTER TABLE knowledge_base
    ADD COLUMN IF NOT EXISTS chunk_index INTEGER NOT NULL DEFAULT 0;

-- Constraint para upsert idempotente
ALTER TABLE knowledge_base
    DROP CONSTRAINT IF EXISTS uq_kb_source_chunk;
ALTER TABLE knowledge_base
    ADD CONSTRAINT uq_kb_source_chunk UNIQUE (source_path, chunk_index);
