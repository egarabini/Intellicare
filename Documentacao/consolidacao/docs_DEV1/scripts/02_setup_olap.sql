-- ============================================================================
-- SCRIPT: Setup PostgreSQL OLAP
-- PROJETO: 02 - Separação Operacional/Analítico
-- DATA: 21/02/2026
-- RESPONSÁVEL: DEV1
-- OBJETIVO: Criar database OLAP com schemas analíticos e anonimização
-- ============================================================================

-- ============================================================================
-- PARTE 1: CRIAR DATABASE E SCHEMAS
-- ============================================================================

-- Conectar como superuser
-- psql -h localhost -U postgres

-- Criar database OLAP
CREATE DATABASE intellicare_olap
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0
    OWNER = postgres;

-- Conectar ao database
\c intellicare_olap

-- Criar schemas analíticos
CREATE SCHEMA IF NOT EXISTS analytics_donabedian;
CREATE SCHEMA IF NOT EXISTS analytics_wanda;

COMMENT ON SCHEMA analytics_donabedian IS 'Dados analíticos anonimizados - Indicadores de Qualidade';
COMMENT ON SCHEMA analytics_wanda IS 'Dados analíticos anonimizados - Gestão de Leitos';

-- ============================================================================
-- PARTE 2: CRIAR USUÁRIO READ-ONLY
-- ============================================================================

-- Criar usuário analytics (somente leitura)
CREATE USER intellicare_analytics WITH PASSWORD 'IntelliCare@2026!OLAP';

-- Conceder permissões no database
GRANT CONNECT ON DATABASE intellicare_olap TO intellicare_analytics;

-- Conceder permissões nos schemas (somente leitura)
GRANT USAGE ON SCHEMA analytics_donabedian TO intellicare_analytics;
GRANT USAGE ON SCHEMA analytics_wanda TO intellicare_analytics;

-- Conceder SELECT em todas as tabelas (presentes e futuras)
GRANT SELECT ON ALL TABLES IN SCHEMA analytics_donabedian TO intellicare_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics_wanda TO intellicare_analytics;

ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_donabedian 
    GRANT SELECT ON TABLES TO intellicare_analytics;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_wanda 
    GRANT SELECT ON TABLES TO intellicare_analytics;

-- ============================================================================
-- PARTE 3: FUNÇÕES DE ANONIMIZAÇÃO
-- ============================================================================

-- Função para gerar hash SHA-256
CREATE OR REPLACE FUNCTION hash_id(id INTEGER)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(digest(id::TEXT, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION hash_id IS 'Gera hash SHA-256 irreversível de um ID';

-- Função para categorizar valores
CREATE OR REPLACE FUNCTION categorizar_valor(valor DECIMAL, baixo DECIMAL, alto DECIMAL)
RETURNS VARCHAR(20) AS $$
BEGIN
    IF valor < baixo THEN
        RETURN 'baixo';
    ELSIF valor > alto THEN
        RETURN 'alto';
    ELSE
        RETURN 'medio';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION categorizar_valor IS 'Categoriza valores em faixas: baixo, médio, alto';

-- Função para generalizar data (manter apenas ano/mês)
CREATE OR REPLACE FUNCTION generalizar_data(data TIMESTAMP)
RETURNS DATE AS $$
BEGIN
    RETURN DATE_TRUNC('month', data)::DATE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION generalizar_data IS 'Generaliza data mantendo apenas ano e mês';

-- ============================================================================
-- PARTE 4: SCHEMA ANALYTICS_DONABEDIAN - FATO MEDIÇÕES
-- ============================================================================

-- Tabela: fato_medicoes (particionada por ano)
CREATE TABLE analytics_donabedian.fato_medicoes (
    id SERIAL,
    indicador_hash VARCHAR(64) NOT NULL,
    indicador_nome VARCHAR(200),
    indicador_tipo VARCHAR(50),
    periodo_ano INTEGER NOT NULL,
    periodo_mes INTEGER NOT NULL,
    periodo_trimestre INTEGER,
    valor_medido DECIMAL(10,2),
    valor_meta DECIMAL(10,2),
    atingiu_meta BOOLEAN,
    faixa_valor VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, periodo_ano)
) PARTITION BY RANGE (periodo_ano);

COMMENT ON TABLE analytics_donabedian.fato_medicoes IS 'Fato de medições de indicadores (anonimizado e particionado)';
COMMENT ON COLUMN analytics_donabedian.fato_medicoes.indicador_hash IS 'Hash SHA-256 do ID do indicador (anonimizado)';
COMMENT ON COLUMN analytics_donabedian.fato_medicoes.faixa_valor IS 'Categorização do valor: baixo, médio, alto';

-- Criar partições por ano
CREATE TABLE analytics_donabedian.fato_medicoes_2024 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2024) TO (2025);

CREATE TABLE analytics_donabedian.fato_medicoes_2025 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2025) TO (2026);

CREATE TABLE analytics_donabedian.fato_medicoes_2026 
    PARTITION OF analytics_donabedian.fato_medicoes
    FOR VALUES FROM (2026) TO (2027);

-- Índices analíticos
CREATE INDEX idx_fato_medicoes_periodo ON analytics_donabedian.fato_medicoes(periodo_ano, periodo_mes);
CREATE INDEX idx_fato_medicoes_tipo ON analytics_donabedian.fato_medicoes(indicador_tipo);
CREATE INDEX idx_fato_medicoes_meta ON analytics_donabedian.fato_medicoes(atingiu_meta);
CREATE INDEX idx_fato_medicoes_faixa ON analytics_donabedian.fato_medicoes(faixa_valor);

-- ============================================================================
-- PARTE 5: SCHEMA ANALYTICS_WANDA - FATO OCUPAÇÕES
-- ============================================================================

-- Tabela: fato_ocupacoes (anonimizada)
CREATE TABLE analytics_wanda.fato_ocupacoes (
    id SERIAL PRIMARY KEY,
    leito_hash VARCHAR(64) NOT NULL,
    paciente_hash VARCHAR(64) NOT NULL,
    setor VARCHAR(100),
    tipo_leito VARCHAR(50),
    data_entrada_ano INTEGER,
    data_entrada_mes INTEGER,
    data_entrada_dia_semana INTEGER,
    tempo_permanencia_dias INTEGER,
    faixa_permanencia VARCHAR(20),
    status_final VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE analytics_wanda.fato_ocupacoes IS 'Fato de ocupações de leitos (anonimizado)';
COMMENT ON COLUMN analytics_wanda.fato_ocupacoes.leito_hash IS 'Hash SHA-256 do ID do leito (anonimizado)';
COMMENT ON COLUMN analytics_wanda.fato_ocupacoes.paciente_hash IS 'Hash SHA-256 do ID do paciente (anonimizado)';
COMMENT ON COLUMN analytics_wanda.fato_ocupacoes.faixa_permanencia IS 'Categorização: curta (<3d), média (3-7d), longa (>7d)';

-- Índices analíticos
CREATE INDEX idx_fato_ocupacoes_periodo ON analytics_wanda.fato_ocupacoes(data_entrada_ano, data_entrada_mes);
CREATE INDEX idx_fato_ocupacoes_setor ON analytics_wanda.fato_ocupacoes(setor);
CREATE INDEX idx_fato_ocupacoes_tipo ON analytics_wanda.fato_ocupacoes(tipo_leito);
CREATE INDEX idx_fato_ocupacoes_faixa ON analytics_wanda.fato_ocupacoes(faixa_permanencia);
CREATE INDEX idx_fato_ocupacoes_dia_semana ON analytics_wanda.fato_ocupacoes(data_entrada_dia_semana);

-- ============================================================================
-- PARTE 6: POLÍTICAS DE RETENÇÃO
-- ============================================================================

-- Função de limpeza de dados antigos (manter 5 anos)
CREATE OR REPLACE FUNCTION analytics_donabedian.cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM analytics_donabedian.fato_medicoes
    WHERE created_at < CURRENT_DATE - INTERVAL '5 years';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Removidos % registros antigos de fato_medicoes', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION analytics_wanda.cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM analytics_wanda.fato_ocupacoes
    WHERE created_at < CURRENT_DATE - INTERVAL '5 years';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Removidos % registros antigos de fato_ocupacoes', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION analytics_donabedian.cleanup_old_data IS 'Remove dados com mais de 5 anos';
COMMENT ON FUNCTION analytics_wanda.cleanup_old_data IS 'Remove dados com mais de 5 anos';

-- ============================================================================
-- PARTE 7: VALIDAÇÕES E ESTATÍSTICAS
-- ============================================================================

-- Validar estrutura criada
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('analytics_donabedian', 'analytics_wanda')
ORDER BY schemaname, tablename;

-- Listar índices criados
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname IN ('analytics_donabedian', 'analytics_wanda')
ORDER BY schemaname, tablename, indexname;

-- Testar funções de anonimização
SELECT 
    'Teste hash_id' AS teste,
    hash_id(123) AS resultado;

SELECT 
    'Teste categorizar_valor' AS teste,
    categorizar_valor(50, 30, 70) AS resultado;

SELECT 
    'Teste generalizar_data' AS teste,
    generalizar_data(CURRENT_TIMESTAMP) AS resultado;

-- ============================================================================
-- SCRIPT CONCLUÍDO
-- ============================================================================

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ Setup OLAP concluído com sucesso!';
    RAISE NOTICE '📊 Database: intellicare_olap';
    RAISE NOTICE '📁 Schemas: analytics_donabedian, analytics_wanda';
    RAISE NOTICE '📋 Tabelas: 2 tabelas fato criadas';
    RAISE NOTICE '🔑 Índices: 9 índices criados';
    RAISE NOTICE '🔒 Anonimização: 3 funções criadas';
    RAISE NOTICE '👤 Usuário: intellicare_analytics (READ-ONLY)';
    RAISE NOTICE '📦 Partições: 3 partições por ano (2024-2026)';
END $$;

