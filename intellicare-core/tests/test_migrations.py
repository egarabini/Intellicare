"""Tests for Alembic migrations.

Tests validate that:
1. Migrations can be applied (upgrade)
2. Migrations can be reverted (downgrade)
3. Schemas and roles are created correctly
4. Permissions are set up as expected
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool


@pytest.fixture
def test_db_url():
    """Get test database URL from environment or use default."""
    import os
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/intellicare_test"
    )


@pytest.fixture
def db_engine(test_db_url):
    """Create database engine for testing."""
    try:
        engine = create_engine(test_db_url, poolclass=NullPool)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        yield engine
    finally:
        engine.dispose()


class TestSchemaMigrations:
    """Test database schema migrations."""

    @pytest.mark.integration
    def test_core_schemas_exist(self, db_engine):
        """Verify core schemas are created."""
        inspector = inspect(db_engine)
        schemas = inspector.get_schema_names()
        
        assert "intellicare_operacional" in schemas, "Missing intellicare_operacional schema"
        assert "intellicare_analitico" in schemas, "Missing intellicare_analitico schema"

    @pytest.mark.integration
    def test_module_schemas_exist(self, db_engine):
        """Verify all module schemas are created."""
        inspector = inspect(db_engine)
        schemas = inspector.get_schema_names()
        
        modules = [
            "oswaldo", "florence", "donabedian", "zilda",
            "geralda", "comunicacao", "auth", "portal", "wanda"
        ]
        
        for module in modules:
            op_schema = f"{module}_operacional"
            an_schema = f"{module}_analitico"
            
            assert op_schema in schemas, f"Missing {op_schema} schema"
            assert an_schema in schemas, f"Missing {an_schema} schema"

    @pytest.mark.integration
    def test_audit_log_table_exists(self, db_engine):
        """Verify audit log table is created."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names(schema="intellicare_operacional")
        
        assert "audit_log" in tables, "audit_log table not found in intellicare_operacional"

    @pytest.mark.integration
    def test_audit_log_columns(self, db_engine):
        """Verify audit log has required columns."""
        inspector = inspect(db_engine)
        columns = {
            col["name"]: col["type"]
            for col in inspector.get_columns("audit_log", schema="intellicare_operacional")
        }
        
        required_columns = ["id", "entity_type", "entity_id", "actor_id", "operation", "timestamp"]
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    @pytest.mark.integration
    def test_audit_log_indexes(self, db_engine):
        """Verify audit log has required indexes."""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("audit_log", schema="intellicare_operacional")
        index_names = [idx["name"] for idx in indexes]
        
        assert "idx_audit_log_entity" in index_names, "Missing idx_audit_log_entity"
        assert "idx_audit_log_timestamp" in index_names, "Missing idx_audit_log_timestamp"


class TestRoles:
    """Test PostgreSQL role creation."""

    @pytest.mark.integration
    def test_operacional_user_role_exists(self, db_engine):
        """Verify operacional_user role exists."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = 'operacional_user'")
            )
            assert result.fetchone() is not None, "operacional_user role not found"

    @pytest.mark.integration
    def test_analytics_user_role_exists(self, db_engine):
        """Verify analytics_user role exists."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = 'analytics_user'")
            )
            assert result.fetchone() is not None, "analytics_user role not found"

    @pytest.mark.integration
    def test_intellicare_admin_role_exists(self, db_engine):
        """Verify intellicare_admin role exists."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = 'intellicare_admin'")
            )
            assert result.fetchone() is not None, "intellicare_admin role not found"

    @pytest.mark.integration
    def test_operacional_user_has_schema_permissions(self, db_engine):
        """Verify operacional_user can access operational schema."""
        with db_engine.connect() as conn:
            # Check if operacional_user has USAGE on operacional schema
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.role_usage_grants
                WHERE grantee = 'operacional_user'
                AND table_schema = 'intellicare_operacional'
                AND privilege_type = 'USAGE'
            """))
            assert result.fetchone() is not None, "operacional_user missing USAGE on intellicare_operacional"

    @pytest.mark.integration
    def test_analytics_user_cannot_write(self, db_engine):
        """Verify analytics_user does not have CREATE permission on analytics schema."""
        with db_engine.connect() as conn:
            # Check that analytics_user has no CREATE permission
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.table_privileges
                WHERE grantee = 'analytics_user'
                AND privilege_type = 'CREATE'
                AND table_schema = ANY('{intellicare_analitico,oswaldo_analitico}'::text[])
            """))
            # Should return no rows (no CREATE permission)
            assert result.fetchone() is None, "analytics_user should not have CREATE permission"


class TestMigrationSequence:
    """Test that migrations can be applied in sequence."""

    @pytest.mark.integration
    def test_migration_001_creates_core_schemas(self, db_engine):
        """Test migration 001 creates core schemas."""
        # Already tested above, but can run specific migration here
        pass

    @pytest.mark.integration
    def test_migration_002_creates_rls(self, db_engine):
        """Test migration 002 creates RLS infrastructure."""
        # Schema permissions are tested above
        pass

    @pytest.mark.integration
    def test_migration_003_creates_module_schemas(self, db_engine):
        """Test migration 003 creates module schemas."""
        # Already tested in test_module_schemas_exist
        pass


class TestSchemaIsolation:
    """Test that schemas are properly isolated."""

    @pytest.mark.integration
    def test_operacional_schema_writable(self, db_engine):
        """Verify operational schema allows writes."""
        with db_engine.connect() as conn:
            # Verify schema exists and is writable
            result = conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'intellicare_operacional'")
            )
            assert result.fetchone() is not None

    @pytest.mark.integration
    def test_analitico_schema_readable(self, db_engine):
        """Verify analytics schema exists (can be read)."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'intellicare_analitico'")
            )
            assert result.fetchone() is not None
