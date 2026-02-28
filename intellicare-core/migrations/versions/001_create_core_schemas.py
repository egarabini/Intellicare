"""001 - Create core module schemas (operacional and analitico).

Revision ID: 001
Revises: None
Create Date: 2026-02-11 12:00:00.000000

This migration creates the base schemas for the Operational/Analytical separation pattern.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create operational and analytics schemas for intellicare_core."""
    # Create operational schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_operacional;")
    
    # Create analytics schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_analitico;")
    
    # Grant usage to public (migrations will set more restrictive permissions)
    op.execute("GRANT USAGE ON SCHEMA intellicare_operacional TO public;")
    op.execute("GRANT USAGE ON SCHEMA intellicare_analitico TO public;")
    
    print("✅ Core schemas created: intellicare_operacional, intellicare_analitico")


def downgrade() -> None:
    """Drop operational and analytics schemas."""
    # Drop schemas with cascade (careful in production!)
    op.execute("DROP SCHEMA IF NOT EXISTS intellicare_analitico CASCADE;")
    op.execute("DROP SCHEMA IF NOT EXISTS intellicare_operacional CASCADE;")
    
    print("❌ Core schemas dropped")
