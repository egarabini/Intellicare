-- ============================================================================
-- NISE TRAINING MODULE - INDEXES
-- ============================================================================
-- Projeto: NISE - Treinamento Assistido
-- Módulo: Database Indexes (Performance Optimization)
-- Versão: 1.0
-- Data: 26/02/2026
-- Responsável: DEV1 + DEV2
-- Objetivo: Performance <100ms P99 para queries
-- ============================================================================

-- ============================================================================
-- 1. ÍNDICES: PATIENTS
-- ============================================================================

-- FHIR ID (usado em JOINs e lookups)
CREATE INDEX IF NOT EXISTS idx_patients_fhir_id 
ON nise_training.patients(fhir_id);

-- CPF (busca por documento)
CREATE INDEX IF NOT EXISTS idx_patients_cpf 
ON nise_training.patients(cpf);

-- CNS (busca por cartão nacional de saúde)
CREATE INDEX IF NOT EXISTS idx_patients_cns 
ON nise_training.patients(cns);

-- Nome (busca por nome)
CREATE INDEX IF NOT EXISTS idx_patients_name 
ON nise_training.patients(name_family, name_given);

-- Data de nascimento (filtros por idade)
CREATE INDEX IF NOT EXISTS idx_patients_birth_date 
ON nise_training.patients(birth_date);

-- Município (filtros geográficos)
CREATE INDEX IF NOT EXISTS idx_patients_municipality 
ON nise_training.patients(municipality_code);

-- JSONB GIN index (queries em dados FHIR)
CREATE INDEX IF NOT EXISTS idx_patients_data_gin 
ON nise_training.patients USING GIN (data);

-- ============================================================================
-- 2. ÍNDICES: OBSERVATIONS
-- ============================================================================

-- FHIR ID
CREATE INDEX IF NOT EXISTS idx_observations_fhir_id 
ON nise_training.observations(fhir_id);

-- Patient (JOIN com patients)
CREATE INDEX IF NOT EXISTS idx_observations_patient 
ON nise_training.observations(patient_fhir_id);

-- Código LOINC (filtro por tipo de exame)
CREATE INDEX IF NOT EXISTS idx_observations_code 
ON nise_training.observations(code_loinc);

-- Data efetiva (ordenação temporal)
CREATE INDEX IF NOT EXISTS idx_observations_datetime 
ON nise_training.observations(effective_datetime DESC);

-- Composto: Patient + Data (query comum)
CREATE INDEX IF NOT EXISTS idx_observations_patient_datetime 
ON nise_training.observations(patient_fhir_id, effective_datetime DESC);

-- JSONB GIN index
CREATE INDEX IF NOT EXISTS idx_observations_data_gin 
ON nise_training.observations USING GIN (data);

-- ============================================================================
-- 3. ÍNDICES: PRACTITIONERS
-- ============================================================================

-- FHIR ID
CREATE INDEX IF NOT EXISTS idx_practitioners_fhir_id 
ON nise_training.practitioners(fhir_id);

-- CPF
CREATE INDEX IF NOT EXISTS idx_practitioners_cpf 
ON nise_training.practitioners(cpf);

-- CRM (busca por registro profissional)
CREATE INDEX IF NOT EXISTS idx_practitioners_crm 
ON nise_training.practitioners(crm);

-- Especialidade (filtro)
CREATE INDEX IF NOT EXISTS idx_practitioners_specialty 
ON nise_training.practitioners(specialty);

-- ============================================================================
-- 4. ÍNDICES: ENCOUNTERS
-- ============================================================================

-- FHIR ID
CREATE INDEX IF NOT EXISTS idx_encounters_fhir_id 
ON nise_training.encounters(fhir_id);

-- Patient (JOIN)
CREATE INDEX IF NOT EXISTS idx_encounters_patient 
ON nise_training.encounters(patient_fhir_id);

-- Practitioner (JOIN)
CREATE INDEX IF NOT EXISTS idx_encounters_practitioner 
ON nise_training.encounters(practitioner_fhir_id);

-- Data início (ordenação temporal)
CREATE INDEX IF NOT EXISTS idx_encounters_start 
ON nise_training.encounters(start_datetime DESC);

-- Tipo de atendimento
CREATE INDEX IF NOT EXISTS idx_encounters_type 
ON nise_training.encounters(encounter_type);

-- ============================================================================
-- 5. ÍNDICES: SCENARIOS
-- ============================================================================

-- Code (lookup único)
CREATE INDEX IF NOT EXISTS idx_scenarios_code 
ON nise_training.scenarios(code);

-- Módulo (filtro)
CREATE INDEX IF NOT EXISTS idx_scenarios_module 
ON nise_training.scenarios(module);

-- Dificuldade (filtro)
CREATE INDEX IF NOT EXISTS idx_scenarios_difficulty 
ON nise_training.scenarios(difficulty);

-- Composto: Módulo + Dificuldade (query comum)
CREATE INDEX IF NOT EXISTS idx_scenarios_module_difficulty 
ON nise_training.scenarios(module, difficulty);

-- Patient (JOIN)
CREATE INDEX IF NOT EXISTS idx_scenarios_patient 
ON nise_training.scenarios(patient_fhir_id);

-- ÍNDICE VETORIAL para RAG (IVFFlat - performance)
CREATE INDEX IF NOT EXISTS idx_scenarios_embedding 
ON nise_training.scenarios 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- ============================================================================
-- 6. ÍNDICES: TRAINING_SESSIONS
-- ============================================================================

-- Session ID (lookup único)
CREATE INDEX IF NOT EXISTS idx_training_sessions_session_id 
ON nise_training.training_sessions(session_id);

-- User ID (histórico do aluno)
CREATE INDEX IF NOT EXISTS idx_training_sessions_user 
ON nise_training.training_sessions(user_id);

-- Scenario (JOIN)
CREATE INDEX IF NOT EXISTS idx_training_sessions_scenario 
ON nise_training.training_sessions(scenario_id);

-- Status (filtro)
CREATE INDEX IF NOT EXISTS idx_training_sessions_status 
ON nise_training.training_sessions(status);

-- Data início (ordenação temporal)
CREATE INDEX IF NOT EXISTS idx_training_sessions_start 
ON nise_training.training_sessions(start_time DESC);

-- Composto: User + Status (query comum)
CREATE INDEX IF NOT EXISTS idx_training_sessions_user_status 
ON nise_training.training_sessions(user_id, status);

-- ============================================================================
-- 7. ÍNDICES: FLOWISE_INTERACTIONS
-- ============================================================================

-- Interaction ID
CREATE INDEX IF NOT EXISTS idx_flowise_interactions_id 
ON nise_training.flowise_interactions(interaction_id);

-- Session (JOIN)
CREATE INDEX IF NOT EXISTS idx_flowise_interactions_session 
ON nise_training.flowise_interactions(session_id);

-- Data (ordenação temporal)
CREATE INDEX IF NOT EXISTS idx_flowise_interactions_created 
ON nise_training.flowise_interactions(created_at DESC);

-- ============================================================================
-- 8. ÍNDICES: KNOWLEDGE_BASES
-- ============================================================================

-- KB ID
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_kb_id 
ON nise_training.knowledge_bases(kb_id);

-- Tipo (filtro)
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_type 
ON nise_training.knowledge_bases(type);

-- ÍNDICE VETORIAL para RAG
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_embedding 
ON nise_training.knowledge_bases 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Full-text search (conteúdo)
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_content_fts 
ON nise_training.knowledge_bases 
USING GIN (to_tsvector('portuguese', content));

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
-- Total de índices criados: 40+
-- Performance esperada: <100ms P99 para queries
-- Próximo script: 04_create_functions.sql (triggers, validações)
-- ============================================================================

