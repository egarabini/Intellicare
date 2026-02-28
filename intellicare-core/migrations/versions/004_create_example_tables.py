"""004 - Create example tables for operational/analytics schemas.

Revision ID: 004
Revises: 003
Create Date: 2026-02-11 12:15:00.000000

This migration creates example tables demonstrating the operational/analytical separation pattern.
Uses oswaldo_operacional and oswaldo_analitico as the example.

Tables created:
- oswaldo_operacional.pacientes: Transactional, with audit metadata
- oswaldo_analitico.pacientes: Denormalized view for reporting

This serves as a template for other modules.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create example tables in oswaldo schemas."""
    
    # ========================================================================
    # OPERATIONAL TABLE: oswaldo_operacional.pacientes
    # ========================================================================
    # This is where transactional writes occur
    # Includes audit metadata and versioning
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS oswaldo_operacional.pacientes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Business data
            nome VARCHAR(255) NOT NULL,
            cpf VARCHAR(14) UNIQUE NOT NULL,
            status VARCHAR(50) DEFAULT 'ativo' CHECK (status IN ('ativo', 'coordenando', 'inativo', 'cancelado')),
            
            -- Audit metadata
            created_by UUID NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_by UUID,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            
            -- Soft delete marker
            valid_to TIMESTAMP WITH TIME ZONE,
            
            -- Optimistic locking
            rowversion INTEGER DEFAULT 1 NOT NULL,
            
            CONSTRAINT chk_valid_to CHECK (
                valid_to IS NULL OR valid_to > created_at
            )
        );
    """)
    
    # Create indexes for operational queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_status 
        ON oswaldo_operacional.pacientes(status)
        WHERE valid_to IS NULL;
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_created_by 
        ON oswaldo_operacional.pacientes(created_by);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_pacientes_updated_at 
        ON oswaldo_operacional.pacientes(updated_at DESC);
    """)
    
    # ========================================================================
    # ANALYTICS TABLE: oswaldo_analitico.pacientes
    # ========================================================================
    # This is where denormalized/aggregated data lives
    # Updated asynchronously via consolidation service
    # Read-only access for BI/reporting
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS oswaldo_analitico.pacientes (
            id UUID PRIMARY KEY,
            
            -- Business data (denormalized)
            nome VARCHAR(255),
            cpf VARCHAR(14),
            status VARCHAR(50),
            
            -- Audit metadata (for tracking consolidation)
            created_by UUID,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_by UUID,
            updated_at TIMESTAMP WITH TIME ZONE,
            
            -- Soft delete marker
            valid_to TIMESTAMP WITH TIME ZONE,
            
            -- Versioning (copied from operacional)
            rowversion INTEGER,
            
            -- Consolidation metadata
            consolidated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            consolidation_source VARCHAR(255) DEFAULT 'EVENT_STREAM'
        );
    """)
    
    # Create indexes for analytics queries (BI-optimized)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_status 
        ON oswaldo_analitico.pacientes(status)
        WHERE valid_to IS NULL;
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_created_at 
        ON oswaldo_analitico.pacientes(created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_oswaldo_analitico_cpf 
        ON oswaldo_analitico.pacientes(cpf);
    """)
    
    # ========================================================================
    # ROW-LEVEL SECURITY (RLS) POLICIES
    # ========================================================================
    # Enforce separation at database level
    
    # Enable RLS on operational table
    op.execute("""
        ALTER TABLE oswaldo_operacional.pacientes ENABLE ROW LEVEL SECURITY;
    """)
    
    # Policy: operacional_user can only access operacional schema
    op.execute("""
        CREATE POLICY operacional_users_can_access 
        ON oswaldo_operacional.pacientes
        FOR ALL
        USING (current_user = 'operacional_user' OR current_user = 'intellicare_admin')
        WITH CHECK (current_user = 'operacional_user' OR current_user = 'intellicare_admin');
    """)
    
    # Enable RLS on analytics table
    op.execute("""
        ALTER TABLE oswaldo_analitico.pacientes ENABLE ROW LEVEL SECURITY;
    """)
    
    # Policy: analytics_user can only SELECT (no INSERT/UPDATE/DELETE)
    op.execute("""
        CREATE POLICY analytics_users_read_only 
        ON oswaldo_analitico.pacientes
        FOR SELECT
        USING (current_user = 'analytics_user' OR current_user = 'intellicare_admin');
    """)
    
    # Policy: Deny INSERT/UPDATE/DELETE on analytics table for everyone except admin
    op.execute("""
        CREATE POLICY analytics_users_deny_write 
        ON oswaldo_analitico.pacientes
        FOR INSERT
        WITH CHECK (current_user = 'intellicare_admin');
    """)
    
    op.execute("""
        CREATE POLICY analytics_users_deny_update 
        ON oswaldo_analitico.pacientes
        FOR UPDATE
        WITH CHECK (current_user = 'intellicare_admin');
    """)
    
    op.execute("""
        CREATE POLICY analytics_users_deny_delete 
        ON oswaldo_analitico.pacientes
        FOR DELETE
        USING (current_user = 'intellicare_admin');
    """)
    
    # ========================================================================
    # TABLE PERMISSIONS
    # ========================================================================
    
    # Operational table
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON oswaldo_operacional.pacientes TO operacional_user;")
    op.execute("GRANT ALL ON oswaldo_operacional.pacientes TO intellicare_admin;")
    op.execute("REVOKE ALL ON oswaldo_operacional.pacientes FROM analytics_user;")
    
    # Analytics table
    op.execute("GRANT SELECT ON oswaldo_analitico.pacientes TO analytics_user;")
    op.execute("GRANT ALL ON oswaldo_analitico.pacientes TO intellicare_admin;")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON oswaldo_analitico.pacientes FROM operacional_user;")
    
    # Grant sequence access
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA oswaldo_operacional TO operacional_user;")
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA oswaldo_operacional TO intellicare_admin;")
    
    print("✅ Example tables created:")
    print("   - oswaldo_operacional.pacientes (transactional)")
    print("   - oswaldo_analitico.pacientes (analytics/denormalized)")
    print("   - RLS policies enforced")
    print("   - Permissions configured")


def downgrade() -> None:
    """Drop example tables."""
    
    # Drop RLS policies first
    op.execute("""
        DROP POLICY IF EXISTS operacional_users_can_access 
        ON oswaldo_operacional.pacientes;
    """)
    
    op.execute("""
        DROP POLICY IF EXISTS analytics_users_read_only 
        ON oswaldo_analitico.pacientes;
    """)
    
    op.execute("""
        DROP POLICY IF EXISTS analytics_users_deny_write 
        ON oswaldo_analitico.pacientes;
    """)
    
    op.execute("""
        DROP POLICY IF EXISTS analytics_users_deny_update 
        ON oswaldo_analitico.pacientes;
    """)
    
    op.execute("""
        DROP POLICY IF EXISTS analytics_users_deny_delete 
        ON oswaldo_analitico.pacientes;
    """)
    
    # Drop tables
    op.execute("DROP TABLE IF EXISTS oswaldo_analitico.pacientes CASCADE;")
    op.execute("DROP TABLE IF EXISTS oswaldo_operacional.pacientes CASCADE;")
    
    print("❌ Example tables dropped")

