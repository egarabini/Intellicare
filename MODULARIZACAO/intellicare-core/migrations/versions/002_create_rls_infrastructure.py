"""002 - Create Row-Level Security (RLS) infrastructure.

Revision ID: 002
Revises: 001
Create Date: 2026-02-11 12:05:00.000000

This migration sets up RLS policies to enforce separation between operational and analytics schemas.
RLS ensures:
- Users can only access their permitted schema
- No cross-schema access via row-level permissions
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Set up RLS policies infrastructure."""
    
    # Create role for operational access
    op.execute("CREATE ROLE operacional_user WITH LOGIN;")
    op.execute("COMMENT ON ROLE operacional_user IS 'User for operational schema (transactional writes)';")
    
    # Create role for analytics access
    op.execute("CREATE ROLE analytics_user WITH LOGIN;")
    op.execute("COMMENT ON ROLE analytics_user IS 'User for analytics schema (read-only, reporting)';")
    
    # Create role for admin/migrations
    op.execute("CREATE ROLE intellicare_admin WITH LOGIN;")
    op.execute("COMMENT ON ROLE intellicare_admin IS 'Admin user for migrations and schema management';")
    
    # Operational user permissions
    op.execute("GRANT USAGE ON SCHEMA intellicare_operacional TO operacional_user;")
    op.execute("GRANT CREATE ON SCHEMA intellicare_operacional TO operacional_user;")
    
    # Analytics user permissions (read-only)
    op.execute("GRANT USAGE ON SCHEMA intellicare_analitico TO analytics_user;")
    # Explicit: NO CREATE permission
    
    # Admin permissions (full access)
    op.execute("GRANT ALL ON SCHEMA intellicare_operacional TO intellicare_admin;")
    op.execute("GRANT ALL ON SCHEMA intellicare_analitico TO intellicare_admin;")
    
    # Create a table for audit logging (in operacional)
    op.execute("""
        CREATE TABLE IF NOT EXISTS intellicare_operacional.audit_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type VARCHAR(255) NOT NULL,
            entity_id VARCHAR(255) NOT NULL,
            actor_id VARCHAR(255) NOT NULL,
            operation VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE
            old_values JSONB,
            new_values JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        );
    """)
    
    # Create index on audit log for fast queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_entity 
        ON intellicare_operacional.audit_log(entity_type, entity_id);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
        ON intellicare_operacional.audit_log(timestamp DESC);
    """)
    
    print("✅ RLS infrastructure created")
    print("   - Roles: operacional_user, analytics_user, intellicare_admin")
    print("   - Audit table: intellicare_operacional.audit_log")


def downgrade() -> None:
    """Remove RLS infrastructure."""
    
    # Drop audit table
    op.execute("DROP TABLE IF NOT EXISTS intellicare_operacional.audit_log CASCADE;")
    
    # Drop roles (revoke permissions first)
    op.execute("REVOKE ALL ON SCHEMA intellicare_operacional FROM operacional_user;")
    op.execute("REVOKE ALL ON SCHEMA intellicare_analitico FROM analytics_user;")
    op.execute("REVOKE ALL ON ALL SCHEMAS FROM intellicare_admin;")
    
    # Drop roles
    op.execute("DROP ROLE IF EXISTS operacional_user;")
    op.execute("DROP ROLE IF EXISTS analytics_user;")
    op.execute("DROP ROLE IF EXISTS intellicare_admin;")
    
    print("❌ RLS infrastructure removed")
