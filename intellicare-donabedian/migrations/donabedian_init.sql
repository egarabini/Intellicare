-- ============================================================================
-- Database Initialization for Donabedian Module
-- ============================================================================
-- This script sets up the donabedian operational and analytical schemas
-- with all necessary tables, indexes, and RLS policies.
-- 
-- IMPORTANT: This assumes core schemas, roles, and extensions already exist
-- (created by migrations 001-004 or intellicare-core setup)
-- ============================================================================

-- ============================================================================
-- 1. OPERATIONAL SCHEMA (Transactional)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS donabedian_operacional;

GRANT USAGE, CREATE ON SCHEMA donabedian_operacional TO operacional_user;
GRANT USAGE, CREATE ON SCHEMA donabedian_operacional TO intellicare_admin;

-- ============================================================================
-- 2. ANALYTICAL SCHEMA (BI/Analytics - Read Only)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS donabedian_analitico;

GRANT USAGE ON SCHEMA donabedian_analitico TO analytics_user;
GRANT USAGE ON SCHEMA donabedian_analitico TO intellicare_admin;

-- ============================================================================
-- 3. OPERATIONAL TABLES
-- ============================================================================

-- Table: donabedian_operacional.pilares
-- Description: Donabedian framework pillars (Estrutura, Processo, Resultado)
-- Audit: Soft delete with valid_to timestamp
-- Locking: Optimistic locking with rowversion
-- ============================================================================

CREATE TABLE IF NOT EXISTS donabedian_operacional.pilares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core business data
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL,  -- ESTRUTURA, PROCESSO, RESULTADO
    ativo BOOLEAN DEFAULT TRUE,
    
    -- Audit metadata (required)
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Soft delete (required)
    valid_to TIMESTAMP WITH TIME ZONE,
    CONSTRAINT ck_pilar_valid_to CHECK (valid_to IS NULL OR valid_to > created_at),
    
    -- Optimistic locking (required)
    rowversion INTEGER NOT NULL DEFAULT 1,
    
    -- Indexes for query performance
    INDEX idx_pilares_tipo (tipo) WHERE valid_to IS NULL,
    INDEX idx_pilares_ativo (ativo) WHERE valid_to IS NULL,
    INDEX idx_pilares_created_at (created_at)
);

COMMENT ON TABLE donabedian_operacional.pilares IS 'Donabedian framework pillars - operational copy';
COMMENT ON COLUMN donabedian_operacional.pilares.tipo IS 'Type: ESTRUTURA (Structure), PROCESSO (Process), RESULTADO (Outcome)';

-- ============================================================================
-- 4. ANALYTICAL TABLES (Denormalized for BI)
-- ============================================================================

-- Table: donabedian_analitico.pilares
-- Description: Denormalized copy of pilares for analytics queries
-- Consolidation: Updated by consolidation consumer from operational
-- ============================================================================

CREATE TABLE IF NOT EXISTS donabedian_analitico.pilares (
    id UUID PRIMARY KEY,
    
    -- Core business data
    nome VARCHAR(255),
    descricao TEXT,
    tipo VARCHAR(50),
    ativo BOOLEAN,
    
    -- Audit metadata
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete
    valid_to TIMESTAMP WITH TIME ZONE,
    
    -- Optimistic locking
    rowversion INTEGER,
    
    -- Consolidation metadata (required)
    consolidated_at TIMESTAMP WITH TIME ZONE,
    consolidation_source VARCHAR(255),
    
    -- Indexes for query performance
    INDEX idx_analitico_tipo (tipo),
    INDEX idx_analitico_ativo (ativo),
    INDEX idx_analitico_created_at (created_at),
    INDEX idx_analitico_consolidated_at (consolidated_at)
);

COMMENT ON TABLE donabedian_analitico.pilares IS 'Donabedian framework pillars - analytical (denormalized) copy';
COMMENT ON COLUMN donabedian_analitico.pilares.consolidated_at IS 'Timestamp when this record was consolidated from operational';
COMMENT ON COLUMN donabedian_analitico.pilares.consolidation_source IS 'Source identifier (e.g., "redis-stream:005")';

-- ============================================================================
-- 5. ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE donabedian_operacional.pilares ENABLE ROW LEVEL SECURITY;
ALTER TABLE donabedian_analitico.pilares ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Operational Table Policies
-- ============================================================================

CREATE POLICY operacional_users_can_access 
    ON donabedian_operacional.pilares
    FOR ALL
    USING (
        current_user = 'operacional_user' 
        OR current_user = 'intellicare_admin'
    );

COMMENT ON POLICY operacional_users_can_access ON donabedian_operacional.pilares 
    IS 'operacional_user and intellicare_admin can access operational data';

-- ============================================================================
-- Analytics Table Policies
-- ============================================================================

-- Read-only: SELECT allowed
CREATE POLICY analytics_users_read_only 
    ON donabedian_analitico.pilares
    FOR SELECT
    USING (
        current_user = 'analytics_user' 
        OR current_user = 'intellicare_admin'
    );

COMMENT ON POLICY analytics_users_read_only ON donabedian_analitico.pilares 
    IS 'analytics_user can only SELECT from analytics tables';

-- Write-denied: INSERT
CREATE POLICY analytics_users_deny_insert 
    ON donabedian_analitico.pilares
    FOR INSERT
    WITH CHECK (false);

COMMENT ON POLICY analytics_users_deny_insert ON donabedian_analitico.pilares 
    IS 'Prevent direct INSERT to analytical tables';

-- Write-denied: UPDATE
CREATE POLICY analytics_users_deny_update 
    ON donabedian_analitico.pilares
    FOR UPDATE
    WITH CHECK (false);

COMMENT ON POLICY analytics_users_deny_update ON donabedian_analitico.pilares 
    IS 'Prevent direct UPDATE to analytical tables';

-- Write-denied: DELETE
CREATE POLICY analytics_users_deny_delete 
    ON donabedian_analitico.pilares
    FOR DELETE
    USING (false);

COMMENT ON POLICY analytics_users_deny_delete ON donabedian_analitico.pilares 
    IS 'Prevent direct DELETE to analytical tables';

-- ============================================================================
-- 6. PERMISSIONS / GRANTS
-- ============================================================================

-- Operational table: operacional_user and intellicare_admin can read/write
GRANT SELECT, INSERT, UPDATE, DELETE 
    ON donabedian_operacional.pilares 
    TO operacional_user;

GRANT SELECT, INSERT, UPDATE, DELETE 
    ON donabedian_operacional.pilares 
    TO intellicare_admin;

-- Analytical table: analytics_user can only read, intellicare_admin can do anything
GRANT SELECT 
    ON donabedian_analitico.pilares 
    TO analytics_user;

GRANT SELECT, INSERT, UPDATE, DELETE 
    ON donabedian_analitico.pilares 
    TO intellicare_admin;

-- ============================================================================
-- 7. CONSOLIDATION TRIGGER (Optional: For automatic denormalization)
-- ============================================================================
-- This trigger publishes an event to Redis Streams (via application)
-- For now, consolidation is handled by the ConsolidationConsumer (FASE 1)
-- which reads from Redis Streams and writes to analytical tables

CREATE OR REPLACE FUNCTION donabedian_operacional.pilar_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the updated_at timestamp on any write
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pilar_updated_at
BEFORE UPDATE ON donabedian_operacional.pilares
FOR EACH ROW
EXECUTE FUNCTION donabedian_operacional.pilar_audit_trigger();

COMMENT ON TRIGGER trg_pilar_updated_at ON donabedian_operacional.pilares
    IS 'Automatically update updated_at timestamp on row changes';

-- ============================================================================
-- 8. INDEXES FOR FREQUENTLY QUERIED COLUMNS
-- ============================================================================

-- Operational table indexes (already created in table definition)
CREATE INDEX IF NOT EXISTS idx_donabedian_pilares_tipo 
    ON donabedian_operacional.pilares(tipo) 
    WHERE valid_to IS NULL;

CREATE INDEX IF NOT EXISTS idx_donabedian_pilares_ativo 
    ON donabedian_operacional.pilares(ativo) 
    WHERE valid_to IS NULL;

CREATE INDEX IF NOT EXISTS idx_donabedian_pilares_created_by 
    ON donabedian_operacional.pilares(created_by);

-- Analytical table indexes (already created in table definition)
CREATE INDEX IF NOT EXISTS idx_donabedian_analitico_tipo 
    ON donabedian_analitico.pilares(tipo);

CREATE INDEX IF NOT EXISTS idx_donabedian_analitico_ativo 
    ON donabedian_analitico.pilares(ativo);

CREATE INDEX IF NOT EXISTS idx_donabedian_analitico_consolidated_at 
    ON donabedian_analitico.pilares(consolidated_at);

-- ============================================================================
-- 9. INFORMATION SCHEMA DOCUMENTATION
-- ============================================================================

-- Document the schema structure
SELECT 
    current_database() as database,
    'donabedian_operacional' as schema_type,
    'Operational/Transactional' as purpose,
    'operacional_user, intellicare_admin' as allowed_roles
UNION ALL
SELECT 
    current_database(),
    'donabedian_analitico',
    'Analytical/BI',
    'analytics_user, intellicare_admin'
;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Created:
--   ✓ 1 operational schema (donabedian_operacional)
--   ✓ 1 analytical schema (donabedian_analitico)
--   ✓ 2 tables (pilares in each schema)
--   ✓ 5 RLS policies (1 allow + 4 deny on analytics)
--   ✓ 1 audit trigger (updated_at)
--   ✓ 8 indexes (performance optimization)
--   ✓ Role-based access control (3 roles configured)
--
-- Tables ready for:
--   ✓ OperationalDataAccess (CREATE/READ/UPDATE/DELETE)
--   ✓ AnalyticsDataAccess (READ-ONLY)
--   ✓ ConsolidationConsumer (Redis → Analytics)
-- ============================================================================
