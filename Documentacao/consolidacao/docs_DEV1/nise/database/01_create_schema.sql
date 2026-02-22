-- ============================================================================
-- NISE TRAINING MODULE - DATABASE SCHEMA
-- ============================================================================
-- Projeto: NISE - Treinamento Assistido
-- Módulo: Database Schema
-- Versão: 1.0
-- Data: 26/02/2026
-- Responsável: DEV1 + DEV2
-- ============================================================================

-- ============================================================================
-- 1. CRIAR SCHEMA DEDICADO
-- ============================================================================
-- Schema separado para isolamento total de produção
CREATE SCHEMA IF NOT EXISTS nise_training;

-- Comentário do schema
COMMENT ON SCHEMA nise_training IS 'Schema dedicado para ambiente de treinamento NISE - isolado de produção';

-- ============================================================================
-- 2. INSTALAR EXTENSÕES NECESSÁRIAS
-- ============================================================================

-- UUID para geração de IDs únicos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pgvector para embeddings e RAG
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- 3. TABELA: PATIENTS (Pacientes Sintéticos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.patients (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Documentos brasileiros
    cpf VARCHAR(11) UNIQUE,
    cns VARCHAR(15) UNIQUE,
    
    -- Dados demográficos
    name_given VARCHAR(100) NOT NULL,
    name_family VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other', 'unknown')),
    
    -- Localização (IBGE)
    municipality_code VARCHAR(7),
    municipality_name VARCHAR(100),
    
    -- FHIR completo (JSONB para flexibilidade)
    data JSONB NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE nise_training.patients IS 'Pacientes sintéticos para treinamento - dados FHIR R4 completos';
COMMENT ON COLUMN nise_training.patients.fhir_id IS 'ID FHIR único do paciente';
COMMENT ON COLUMN nise_training.patients.cpf IS 'CPF válido (algoritmo módulo 11)';
COMMENT ON COLUMN nise_training.patients.cns IS 'CNS válido (Cartão Nacional de Saúde)';
COMMENT ON COLUMN nise_training.patients.data IS 'Recurso FHIR Patient completo em JSON';

-- ============================================================================
-- 4. TABELA: OBSERVATIONS (Observações/Exames)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.observations (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    patient_fhir_id VARCHAR(64) NOT NULL,
    
    -- Códigos padronizados
    code_loinc VARCHAR(20) NOT NULL,
    code_display VARCHAR(200),
    
    -- Valores
    value_quantity NUMERIC(10,2),
    value_unit VARCHAR(50),
    
    -- Temporal
    effective_datetime TIMESTAMP NOT NULL,
    
    -- FHIR completo
    data JSONB NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key
    FOREIGN KEY (patient_fhir_id) REFERENCES nise_training.patients(fhir_id) ON DELETE CASCADE
);

-- Comentários
COMMENT ON TABLE nise_training.observations IS 'Observações clínicas (exames, sinais vitais) - FHIR R4';
COMMENT ON COLUMN nise_training.observations.code_loinc IS 'Código LOINC do exame/observação';
COMMENT ON COLUMN nise_training.observations.data IS 'Recurso FHIR Observation completo em JSON';

-- ============================================================================
-- 5. TABELA: PRACTITIONERS (Profissionais de Saúde)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.practitioners (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Documentos
    cpf VARCHAR(11) UNIQUE,
    cns VARCHAR(15) UNIQUE,
    
    -- Dados pessoais
    name_given VARCHAR(100) NOT NULL,
    name_family VARCHAR(100) NOT NULL,
    
    -- Dados profissionais
    specialty VARCHAR(100),
    crm VARCHAR(20),
    
    -- FHIR completo
    data JSONB NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE nise_training.practitioners IS 'Profissionais de saúde sintéticos - FHIR R4';
COMMENT ON COLUMN nise_training.practitioners.specialty IS 'Especialidade médica';
COMMENT ON COLUMN nise_training.practitioners.crm IS 'Registro profissional (CRM, COREN, etc)';

-- ============================================================================
-- 6. TABELA: ENCOUNTERS (Consultas/Atendimentos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nise_training.encounters (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    patient_fhir_id VARCHAR(64) NOT NULL,
    practitioner_fhir_id VARCHAR(64) NOT NULL,
    
    -- Tipo de atendimento
    encounter_type VARCHAR(50) NOT NULL,
    
    -- Temporal
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    
    -- FHIR completo
    data JSONB NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign keys
    FOREIGN KEY (patient_fhir_id) REFERENCES nise_training.patients(fhir_id) ON DELETE CASCADE,
    FOREIGN KEY (practitioner_fhir_id) REFERENCES nise_training.practitioners(fhir_id) ON DELETE CASCADE
);

-- Comentários
COMMENT ON TABLE nise_training.encounters IS 'Consultas e atendimentos - FHIR R4';
COMMENT ON COLUMN nise_training.encounters.encounter_type IS 'Tipo de atendimento (ambulatorial, emergência, etc)';

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
-- Total de tabelas criadas: 4
-- Próximo script: 02_create_training_tables.sql (scenarios, training_sessions)
-- ============================================================================

