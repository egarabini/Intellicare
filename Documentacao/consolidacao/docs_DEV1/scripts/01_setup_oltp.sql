-- ============================================================================
-- SCRIPT: Setup PostgreSQL OLTP
-- PROJETO: 02 - Separação Operacional/Analítico
-- DATA: 20/02/2026
-- RESPONSÁVEL: DEV1
-- OBJETIVO: Criar database OLTP com schemas e tabelas operacionais
-- ============================================================================

-- ============================================================================
-- PARTE 1: CRIAR DATABASE E SCHEMAS
-- ============================================================================

-- Conectar como superuser
-- psql -h localhost -U postgres

-- Criar database OLTP
CREATE DATABASE intellicare_oltp
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0
    OWNER = postgres;

-- Conectar ao database
\c intellicare_oltp

-- Criar schemas para módulos
CREATE SCHEMA IF NOT EXISTS donabedian;
CREATE SCHEMA IF NOT EXISTS wanda;

COMMENT ON SCHEMA donabedian IS 'Módulo de Indicadores de Qualidade (Donabedian)';
COMMENT ON SCHEMA wanda IS 'Módulo de Gestão de Leitos (Wanda)';

-- ============================================================================
-- PARTE 2: CRIAR USUÁRIO E PERMISSÕES
-- ============================================================================

-- Criar usuário da aplicação
CREATE USER intellicare_app WITH PASSWORD 'IntelliCare@2026!OLTP';

-- Conceder permissões no database
GRANT CONNECT ON DATABASE intellicare_oltp TO intellicare_app;

-- Conceder permissões nos schemas
GRANT USAGE ON SCHEMA donabedian TO intellicare_app;
GRANT USAGE ON SCHEMA wanda TO intellicare_app;

-- Conceder permissões em tabelas (presentes e futuras)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA donabedian TO intellicare_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA wanda TO intellicare_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA donabedian 
    GRANT ALL ON TABLES TO intellicare_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA wanda 
    GRANT ALL ON TABLES TO intellicare_app;

-- Conceder permissões em sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA donabedian TO intellicare_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA wanda TO intellicare_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA donabedian 
    GRANT ALL ON SEQUENCES TO intellicare_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA wanda 
    GRANT ALL ON SEQUENCES TO intellicare_app;

-- ============================================================================
-- PARTE 3: SCHEMA DONABEDIAN - INDICADORES DE QUALIDADE
-- ============================================================================

-- Tabela: indicadores
CREATE TABLE donabedian.indicadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('estrutura', 'processo', 'resultado')),
    formula TEXT,
    meta_valor DECIMAL(10,2),
    meta_unidade VARCHAR(20),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

COMMENT ON TABLE donabedian.indicadores IS 'Indicadores de qualidade baseados no modelo Donabedian';
COMMENT ON COLUMN donabedian.indicadores.tipo IS 'Tipo do indicador: estrutura, processo ou resultado';

-- Tabela: medicoes
CREATE TABLE donabedian.medicoes (
    id SERIAL PRIMARY KEY,
    indicador_id INTEGER NOT NULL REFERENCES donabedian.indicadores(id) ON DELETE CASCADE,
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    valor_medido DECIMAL(10,2) NOT NULL,
    valor_meta DECIMAL(10,2),
    atingiu_meta BOOLEAN,
    observacoes TEXT,
    responsavel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT chk_periodo CHECK (periodo_fim >= periodo_inicio)
);

COMMENT ON TABLE donabedian.medicoes IS 'Medições dos indicadores de qualidade';

-- Tabela: planos_acao
CREATE TABLE donabedian.planos_acao (
    id SERIAL PRIMARY KEY,
    medicao_id INTEGER NOT NULL REFERENCES donabedian.medicoes(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    prazo DATE,
    status VARCHAR(50) DEFAULT 'pendente' CHECK (status IN ('pendente', 'em_andamento', 'concluido', 'cancelado')),
    responsavel_id INTEGER,
    data_conclusao DATE,
    resultado TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

COMMENT ON TABLE donabedian.planos_acao IS 'Planos de ação para indicadores que não atingiram a meta';

-- Índices para performance - Donabedian
CREATE INDEX idx_medicoes_indicador ON donabedian.medicoes(indicador_id);
CREATE INDEX idx_medicoes_periodo ON donabedian.medicoes(periodo_inicio, periodo_fim);
CREATE INDEX idx_medicoes_atingiu_meta ON donabedian.medicoes(atingiu_meta);
CREATE INDEX idx_planos_medicao ON donabedian.planos_acao(medicao_id);
CREATE INDEX idx_planos_status ON donabedian.planos_acao(status);

-- ============================================================================
-- PARTE 4: SCHEMA WANDA - GESTÃO DE LEITOS
-- ============================================================================

-- Tabela: leitos
CREATE TABLE wanda.leitos (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(20) NOT NULL UNIQUE,
    setor VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('UTI', 'enfermaria', 'isolamento', 'observacao')),
    status VARCHAR(50) DEFAULT 'disponivel' CHECK (status IN ('disponivel', 'ocupado', 'manutencao', 'bloqueado')),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

COMMENT ON TABLE wanda.leitos IS 'Cadastro de leitos hospitalares';
COMMENT ON COLUMN wanda.leitos.tipo IS 'Tipo do leito: UTI, enfermaria, isolamento, observacao';

-- Tabela: ocupacoes
CREATE TABLE wanda.ocupacoes (
    id SERIAL PRIMARY KEY,
    leito_id INTEGER NOT NULL REFERENCES wanda.leitos(id) ON DELETE RESTRICT,
    paciente_id INTEGER NOT NULL,
    data_entrada TIMESTAMP NOT NULL,
    data_saida TIMESTAMP,
    motivo_internacao TEXT,
    status VARCHAR(50) DEFAULT 'ativo' CHECK (status IN ('ativo', 'alta', 'transferido', 'obito')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT chk_datas CHECK (data_saida IS NULL OR data_saida >= data_entrada)
);

COMMENT ON TABLE wanda.ocupacoes IS 'Histórico de ocupações de leitos';

-- Tabela: transferencias
CREATE TABLE wanda.transferencias (
    id SERIAL PRIMARY KEY,
    ocupacao_id INTEGER NOT NULL REFERENCES wanda.ocupacoes(id) ON DELETE CASCADE,
    leito_origem_id INTEGER NOT NULL REFERENCES wanda.leitos(id),
    leito_destino_id INTEGER NOT NULL REFERENCES wanda.leitos(id),
    data_transferencia TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo TEXT,
    responsavel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT chk_leitos_diferentes CHECK (leito_origem_id != leito_destino_id)
);

COMMENT ON TABLE wanda.transferencias IS 'Histórico de transferências entre leitos';

-- Índices para performance - Wanda
CREATE INDEX idx_leitos_setor ON wanda.leitos(setor);
CREATE INDEX idx_leitos_tipo ON wanda.leitos(tipo);
CREATE INDEX idx_leitos_status ON wanda.leitos(status);
CREATE INDEX idx_ocupacoes_leito ON wanda.ocupacoes(leito_id);
CREATE INDEX idx_ocupacoes_paciente ON wanda.ocupacoes(paciente_id);
CREATE INDEX idx_ocupacoes_datas ON wanda.ocupacoes(data_entrada, data_saida);
CREATE INDEX idx_ocupacoes_status ON wanda.ocupacoes(status);
CREATE INDEX idx_transferencias_ocupacao ON wanda.transferencias(ocupacao_id);

-- ============================================================================
-- PARTE 5: FUNÇÕES DE AUDITORIA
-- ============================================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at - Donabedian
CREATE TRIGGER trg_indicadores_updated_at
    BEFORE UPDATE ON donabedian.indicadores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_medicoes_updated_at
    BEFORE UPDATE ON donabedian.medicoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_planos_acao_updated_at
    BEFORE UPDATE ON donabedian.planos_acao
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para updated_at - Wanda
CREATE TRIGGER trg_leitos_updated_at
    BEFORE UPDATE ON wanda.leitos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ocupacoes_updated_at
    BEFORE UPDATE ON wanda.ocupacoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- PARTE 6: VALIDAÇÕES E ESTATÍSTICAS
-- ============================================================================

-- Validar estrutura criada
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('donabedian', 'wanda')
ORDER BY schemaname, tablename;

-- Listar índices criados
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname IN ('donabedian', 'wanda')
ORDER BY schemaname, tablename, indexname;

-- ============================================================================
-- SCRIPT CONCLUÍDO
-- ============================================================================

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ Setup OLTP concluído com sucesso!';
    RAISE NOTICE '📊 Database: intellicare_oltp';
    RAISE NOTICE '📁 Schemas: donabedian, wanda';
    RAISE NOTICE '📋 Tabelas: 6 tabelas criadas';
    RAISE NOTICE '🔑 Índices: 13 índices criados';
    RAISE NOTICE '👤 Usuário: intellicare_app';
END $$;

