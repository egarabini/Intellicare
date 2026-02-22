-- ============================================================================
-- NISE TRAINING MODULE - TRAINING TABLES
-- ============================================================================
-- Projeto: NISE - Treinamento Assistido
-- Módulo: Training Tables (Scenarios, Sessions)
-- Versão: 1.0
-- Data: 26/02/2026
-- Responsável: DEV1 + DEV2
-- ============================================================================

-- ============================================================================
-- 1. TABELA: SCENARIOS (Cenários Clínicos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.scenarios (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Descrição
    title VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Classificação
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('basic', 'intermediate', 'advanced')),
    module VARCHAR(50) NOT NULL CHECK (module IN ('florence', 'oswaldo', 'geralda', 'wanda')),
    
    -- Paciente associado
    patient_fhir_id VARCHAR(64),
    
    -- Avaliação
    expected_actions JSONB NOT NULL,
    evaluation_criteria JSONB NOT NULL,
    
    -- RAG (Flowise)
    embedding vector(1536),  -- OpenAI embeddings dimension
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (patient_fhir_id) REFERENCES nise_training.patients(fhir_id) ON DELETE SET NULL
);

-- Comentários
COMMENT ON TABLE nise_training.scenarios IS 'Cenários clínicos estruturados para treinamento';
COMMENT ON COLUMN nise_training.scenarios.code IS 'Código único do cenário (ex: SCEN-FLOR-001)';
COMMENT ON COLUMN nise_training.scenarios.difficulty IS 'Nível de dificuldade: basic, intermediate, advanced';
COMMENT ON COLUMN nise_training.scenarios.module IS 'Módulo INTELLICARE: florence, oswaldo, geralda, wanda';
COMMENT ON COLUMN nise_training.scenarios.expected_actions IS 'Ações esperadas do aluno (JSON)';
COMMENT ON COLUMN nise_training.scenarios.evaluation_criteria IS 'Critérios de avaliação (JSON)';
COMMENT ON COLUMN nise_training.scenarios.embedding IS 'Embedding vetorial para RAG (Flowise)';

-- ============================================================================
-- 2. TABELA: TRAINING_SESSIONS (Sessões de Treinamento)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.training_sessions (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    
    -- Usuário
    user_id VARCHAR(100) NOT NULL,
    
    -- Cenário
    scenario_id INTEGER NOT NULL,
    
    -- Temporal
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    
    -- Execução
    actions_taken JSONB,  -- Ações realizadas pelo aluno
    
    -- Avaliação
    score NUMERIC(5,2),  -- Pontuação (0-100)
    feedback JSONB,  -- Feedback automático (Flowise LLM)
    
    -- Status
    status VARCHAR(20) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (scenario_id) REFERENCES nise_training.scenarios(id) ON DELETE CASCADE
);

-- Comentários
COMMENT ON TABLE nise_training.training_sessions IS 'Sessões de treinamento dos alunos';
COMMENT ON COLUMN nise_training.training_sessions.session_id IS 'UUID único da sessão';
COMMENT ON COLUMN nise_training.training_sessions.user_id IS 'ID do usuário/aluno';
COMMENT ON COLUMN nise_training.training_sessions.actions_taken IS 'Ações realizadas durante a sessão (JSON)';
COMMENT ON COLUMN nise_training.training_sessions.score IS 'Pontuação final (0-100)';
COMMENT ON COLUMN nise_training.training_sessions.feedback IS 'Feedback gerado por Flowise LLM (JSON)';
COMMENT ON COLUMN nise_training.training_sessions.status IS 'Status: in_progress, completed, abandoned';

-- ============================================================================
-- 3. TABELA: FLOWISE_INTERACTIONS (Interações com Chatbot)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.flowise_interactions (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    interaction_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    
    -- Sessão associada
    session_id UUID NOT NULL,
    
    -- Interação
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    
    -- Contexto RAG
    rag_sources JSONB,  -- Fontes usadas pelo RAG
    
    -- Temporal
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (session_id) REFERENCES nise_training.training_sessions(session_id) ON DELETE CASCADE
);

-- Comentários
COMMENT ON TABLE nise_training.flowise_interactions IS 'Interações com chatbot "Dr. Nise" (Flowise)';
COMMENT ON COLUMN nise_training.flowise_interactions.user_message IS 'Pergunta do aluno';
COMMENT ON COLUMN nise_training.flowise_interactions.bot_response IS 'Resposta do chatbot Flowise';
COMMENT ON COLUMN nise_training.flowise_interactions.rag_sources IS 'Fontes RAG usadas (guidelines, casos, etc)';

-- ============================================================================
-- 4. TABELA: KNOWLEDGE_BASES (Bases de Conhecimento para RAG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.knowledge_bases (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Descrição
    name VARCHAR(200) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('guideline', 'protocol', 'case', 'reference')),
    
    -- Conteúdo
    content TEXT NOT NULL,
    metadata JSONB,
    
    -- RAG
    embedding vector(1536),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE nise_training.knowledge_bases IS 'Bases de conhecimento para RAG (guidelines, protocolos, casos)';
COMMENT ON COLUMN nise_training.knowledge_bases.type IS 'Tipo: guideline, protocol, case, reference';
COMMENT ON COLUMN nise_training.knowledge_bases.content IS 'Conteúdo textual para RAG';
COMMENT ON COLUMN nise_training.knowledge_bases.embedding IS 'Embedding vetorial para busca semântica';

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
-- Total de tabelas criadas: 4 (scenarios, training_sessions, flowise_interactions, knowledge_bases)
-- Total geral: 8 tabelas
-- Próximo script: 03_create_indexes.sql
-- ============================================================================

