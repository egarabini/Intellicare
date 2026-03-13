-- IntelliCare V3 - Inicializacao do PostgreSQL
-- Executado automaticamente pelo container na primeira inicializacao

-- Extensoes
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Banco do Keycloak
CREATE DATABASE keycloak
    WITH OWNER = intellicare
    ENCODING = 'UTF8';

-- Schema de desenvolvimento (tenant ficticio para testes locais)
CREATE SCHEMA IF NOT EXISTS tenant_dev;

-- Tabela knowledge_base no tenant_dev (para ingestao imediata dos docs)
CREATE TABLE IF NOT EXISTS tenant_dev.knowledge_base (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_path     TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL DEFAULT 0,
    embedding       vector(768),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (source_path, chunk_index)
);

-- Indice HNSW para busca semantica
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx
    ON tenant_dev.knowledge_base
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS knowledge_base_updated_at ON tenant_dev.knowledge_base;

CREATE TRIGGER knowledge_base_updated_at
    BEFORE UPDATE ON tenant_dev.knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
