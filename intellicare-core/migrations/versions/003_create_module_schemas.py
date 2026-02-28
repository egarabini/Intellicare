"""003 - Create module-specific operational and analytics schemas.

Revision ID: 003
Revises: 002
Create Date: 2026-02-11 12:10:00.000000

This migration creates schemas for all IntelliCare modules:
- oswaldo (patient monitoring)
- florence (clinical management)
- donabedian (quality metrics)
- zilda (clinical assistant)
- geralda (configuration)
- comunicacao (communication/CPaaS)
- auth (authentication)
- portal (web interface)
- wanda (orchestration)

Each module gets TWO schemas:
- {module}_operacional: Transactional, real-time writes
- {module}_analitico: Denormalized, read-only, eventual consistency
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


# List of modules requiring operational/analytical separation
MODULES = [
    "oswaldo",
    "florence",
    "donabedian",
    "zilda",
    "geralda",
    "comunicacao",
    "auth",
    "portal",
    "wanda",
]


def upgrade() -> None:
    """Create operational and analytics schemas for all modules."""
    
    for module in MODULES:
        operational_schema = f"{module}_operacional"
        analytics_schema = f"{module}_analitico"
        
        # Create operational schema
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {operational_schema};")
        op.execute(f"COMMENT ON SCHEMA {operational_schema} IS 'Operational data for {module} module';")
        
        # Create analytics schema
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {analytics_schema};")
        op.execute(f"COMMENT ON SCHEMA {analytics_schema} IS 'Analytics/denormalized data for {module} module';")
        
        # Grant permissions to operacional_user
        op.execute(f"GRANT USAGE ON SCHEMA {operational_schema} TO operacional_user;")
        op.execute(f"GRANT CREATE ON SCHEMA {operational_schema} TO operacional_user;")
        
        # Grant read-only permissions to analytics_user
        op.execute(f"GRANT USAGE ON SCHEMA {analytics_schema} TO analytics_user;")
        # Explicitly NO CREATE for analytics_user
        
        # Grant admin permissions
        op.execute(f"GRANT ALL ON SCHEMA {operational_schema} TO intellicare_admin;")
        op.execute(f"GRANT ALL ON SCHEMA {analytics_schema} TO intellicare_admin;")
        
        print(f"✅ Created schemas for {module}: {operational_schema}, {analytics_schema}")
    
    print(f"✅ All {len(MODULES)} module schemas created")


def downgrade() -> None:
    """Drop all module schemas."""
    
    for module in MODULES:
        operational_schema = f"{module}_operacional"
        analytics_schema = f"{module}_analitico"
        
        # Revoke permissions
        op.execute(f"REVOKE ALL ON SCHEMA {operational_schema} FROM operacional_user;")
        op.execute(f"REVOKE ALL ON SCHEMA {analytics_schema} FROM analytics_user;")
        op.execute(f"REVOKE ALL ON SCHEMA {operational_schema} FROM intellicare_admin;")
        op.execute(f"REVOKE ALL ON SCHEMA {analytics_schema} FROM intellicare_admin;")
        
        # Drop schemas with cascade
        op.execute(f"DROP SCHEMA IF NOT EXISTS {analytics_schema} CASCADE;")
        op.execute(f"DROP SCHEMA IF NOT EXISTS {operational_schema} CASCADE;")
        
        print(f"❌ Dropped schemas for {module}")
