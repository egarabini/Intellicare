-- ============================================================================
-- Database Initialization Script for IntelliCare FASE 1
-- Runs automatically when PostgreSQL container starts
-- ============================================================================

-- Create intellicare_db database (if starting fresh)
-- Note: The POSTGRES_DB env var already creates it, this is for clarity

-- ============================================================================
-- Apply all migrations from STEP 1.3
-- ============================================================================

-- MIGRATION 001: Core Schemas
CREATE SCHEMA IF NOT EXISTS intellicare_operacional;
CREATE SCHEMA IF NOT EXISTS intellicare_analitico;

GRANT USAGE ON SCHEMA intellicare_operacional TO PUBLIC;
GRANT USAGE ON SCHEMA intellicare_analitico TO PUBLIC;

-- ============================================================================
-- MIGRATION 002: RLS Infrastructure + Roles
-- ============================================================================

-- Create roles
CREATE ROLE operacional_user WITH LOGIN;
ALTER ROLE operacional_user WITH PASSWORD 'operacional_pwd';
ALTER ROLE operacional_user SET statement_timeout = '30s';

CREATE ROLE analytics_user WITH LOGIN;
ALTER ROLE analytics_user WITH PASSWORD 'analytics_pwd';
ALTER ROLE analytics_user SET statement_timeout = '60s';
ALTER ROLE analytics_user SET default_transaction_isolation = 'READ ONLY';

CREATE ROLE intellicare_admin WITH LOGIN SUPERUSER;
ALTER ROLE intellicare_admin WITH PASSWORD 'intellicare_dev_pwd';
ALTER ROLE intellicare_admin SET statement_timeout = '120s';

-- Grant schema permissions
GRANT USAGE, CREATE ON SCHEMA intellicare_operacional TO operacional_user;
GRANT USAGE, CREATE ON SCHEMA intellicare_operacional TO intellicare_admin;

GRANT USAGE ON SCHEMA intellicare_analitico TO analytics_user;
GRANT USAGE ON SCHEMA intellicare_analitico TO intellicare_admin;

-- Create audit log table
CREATE TABLE IF NOT EXISTS intellicare_operacional.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(255) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT
);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_entity 
    ON intellicare_operacional.audit_log (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
    ON intellicare_operacional.audit_log (timestamp DESC);

-- Grant permissions
GRANT SELECT, INSERT ON intellicare_operacional.audit_log TO operacional_user;
GRANT SELECT ON intellicare_operacional.audit_log TO analytics_user;

-- ============================================================================
-- MIGRATION 003: Module Schemas
-- ============================================================================

DO $$
DECLARE
  modules TEXT[] := ARRAY[
    'oswaldo', 'florence', 'donabedian', 'zilda', 'geralda',
    'comunicacao', 'auth', 'portal', 'wanda'
  ];
  module TEXT;
BEGIN
  FOREACH module IN ARRAY modules LOOP
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', module || '_operacional');
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', module || '_analitico');
    
    EXECUTE format('GRANT USAGE, CREATE ON SCHEMA %I TO operacional_user', 
      module || '_operacional');
    EXECUTE format('GRANT USAGE, CREATE ON SCHEMA %I TO intellicare_admin', 
      module || '_operacional');
    
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO analytics_user', 
      module || '_analitico');
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO intellicare_admin', 
      module || '_analitico');
  END LOOP;
END $$;

-- ============================================================================
-- MIGRATION 004: Example Tables (oswaldo.pacientes)
-- ============================================================================

-- Create operational table
CREATE TABLE IF NOT EXISTS oswaldo_operacional.pacientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'ativo',
    
    -- Audit metadata
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Soft delete
    valid_to TIMESTAMP WITH TIME ZONE DEFAULT NULL CHECK (valid_to IS NULL OR valid_to > created_at),
    
    -- Optimistic locking
    rowversion INTEGER DEFAULT 1
);

-- Create analytics table
CREATE TABLE IF NOT EXISTS oswaldo_analitico.pacientes (
    id UUID PRIMARY KEY,
    nome VARCHAR(255),
    cpf VARCHAR(14),
    status VARCHAR(50),
    
    -- Audit metadata
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete
    valid_to TIMESTAMP WITH TIME ZONE,
    
    -- Optimistic locking
    rowversion INTEGER,
    
    -- Consolidation metadata
    consolidated_at TIMESTAMP WITH TIME ZONE,
    consolidation_source VARCHAR(255)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_status 
    ON oswaldo_operacional.pacientes (status) WHERE valid_to IS NULL;
CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_created_by 
    ON oswaldo_operacional.pacientes (created_by);
CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_updated_at 
    ON oswaldo_operacional.pacientes (updated_at DESC) WHERE valid_to IS NULL;

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_status 
    ON oswaldo_analitico.pacientes (status);
CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_created_at 
    ON oswaldo_analitico.pacientes (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_cpf 
    ON oswaldo_analitico.pacientes (cpf);

-- Enable RLS
ALTER TABLE oswaldo_operacional.pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE oswaldo_analitico.pacientes ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for operational table
CREATE POLICY IF NOT EXISTS operacional_users_can_access 
    ON oswaldo_operacional.pacientes
    FOR ALL
    USING (current_user = 'operacional_user' OR current_user = 'intellicare_admin');

-- Create RLS policies for analytics table
CREATE POLICY IF NOT EXISTS analytics_users_read_only 
    ON oswaldo_analitico.pacientes
    FOR SELECT
    USING (current_user = 'analytics_user' OR current_user = 'intellicare_admin');

CREATE POLICY IF NOT EXISTS analytics_users_deny_write 
    ON oswaldo_analitico.pacientes
    FOR INSERT
    WITH CHECK (false);

CREATE POLICY IF NOT EXISTS analytics_users_deny_update 
    ON oswaldo_analitico.pacientes
    FOR UPDATE
    WITH CHECK (false);

CREATE POLICY IF NOT EXISTS analytics_users_deny_delete 
    ON oswaldo_analitico.pacientes
    FOR DELETE
    USING (false);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE oswaldo_operacional.pacientes 
    TO operacional_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE oswaldo_operacional.pacientes 
    TO intellicare_admin;

GRANT SELECT ON TABLE oswaldo_analitico.pacientes TO analytics_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE oswaldo_analitico.pacientes 
    TO intellicare_admin;

-- ============================================================================
-- TEST DATA - Sample pacientes for E2E testing
-- ============================================================================

-- Only insert if table is empty
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM oswaldo_operacional.pacientes) = 0 THEN
    INSERT INTO oswaldo_operacional.pacientes 
      (id, nome, cpf, status, created_by, updated_by)
    VALUES
      ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'José Silva', '12345678901', 'ativo', 
       '550e8400-e29b-41d4-a716-446655440000'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID),
      ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'Maria Santos', '23456789012', 'ativo',
       '550e8400-e29b-41d4-a716-446655440000'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID),
      ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'João Castro', '34567890123', 'inativo',
       '550e8400-e29b-41d4-a716-446655440000'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID);
  END IF;
END $$;

-- ============================================================================
-- Extensions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================================
-- Summary
-- ============================================================================
-- Schemas created: 20 (2 core + 18 module)
-- Tables created: 3 (audit_log, pacientes op, pacientes analytics)
-- Roles created: 3 (operacional_user, analytics_user, intellicare_admin)
-- Policies created: 5 RLS policies
-- ============================================================================
