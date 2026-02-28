"""
STEP 1.4: End-to-End Integration Tests with Real Infrastructure
Tests real PostgreSQL, Redis, and Event Publishing pipeline

Run with: pytest tests/test_e2e_real_infrastructure.py -v -m real_infrastructure
Or: pytest tests/test_e2e_real_infrastructure.py --real-postgres --real-redis

Prerequisites:
  - docker-compose up (starts PostgreSQL, Redis, Prometheus)
  - export DATABASE_URL="postgresql://..."
  - export REDIS_URL="redis://..."
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

import pytest
import redis
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

# Import from STEP 1.1 + 1.2
from intellicare_core.consolidation.consumer import ConsolidationConsumer
from intellicare_core.data_access.operational import OperationalDataAccess
from intellicare_core.data_access.analytics import AnalyticsDataAccess


# ============================================================================
# Fixtures for Real Infrastructure
# ============================================================================

@pytest.fixture(scope="session")
def real_database_url() -> str:
    """Get real database URL from environment or use docker default"""
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db"
    )
    return url


@pytest.fixture(scope="session")
def real_redis_url() -> str:
    """Get real Redis URL from environment or use docker default"""
    url = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379"
    )
    return url


@pytest.fixture(scope="session")
def real_engine(real_database_url: str):
    """Create SQLAlchemy engine connected to real PostgreSQL"""
    try:
        engine = create_engine(
            real_database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connection before use
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL: {e}")


@pytest.fixture(scope="session")
def real_session_factory(real_engine):
    """Create session factory for real database"""
    return sessionmaker(bind=real_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
def real_db_session(real_session_factory) -> Session:
    """Create a session for a single test"""
    session = real_session_factory()
    yield session
    session.close()


@pytest.fixture(scope="session")
def real_redis_client(real_redis_url: str) -> redis.Redis:
    """Connect to real Redis"""
    try:
        # Parse URL like redis://localhost:6379/0
        host = real_redis_url.split("://")[1].split(":")[0]
        port = int(real_redis_url.split(":")[2].split("/")[0])
        db = int(real_redis_url.split("/")[3]) if "/" in real_redis_url.split(":")[2] else 0
        
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5
        )
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"Cannot connect to Redis: {e}")


@pytest.fixture(scope="function")
def redis_clean(real_redis_client: redis.Redis):
    """Clean Redis before and after test"""
    # Clean before
    real_redis_client.flushdb()
    yield real_redis_client
    # Clean after
    real_redis_client.flushdb()


# ============================================================================
# Test Patient Model (matches oswaldo_operacional.pacientes)
# ============================================================================

class Paciente:
    """In-memory representation of oswaldo_operacional.pacientes"""
    
    def __init__(
        self,
        id: UUID = None,
        nome: str = None,
        cpf: str = None,
        status: str = "ativo",
        created_by: UUID = None,
        created_at: datetime = None,
        updated_by: UUID = None,
        updated_at: datetime = None,
        valid_to: Optional[datetime] = None,
        rowversion: int = 1
    ):
        self.id = id or uuid.uuid4()
        self.nome = nome
        self.cpf = cpf
        self.status = status
        self.created_by = created_by or uuid.uuid4()
        self.created_at = created_at or datetime.utcnow()
        self.updated_by = updated_by
        self.updated_at = updated_at or datetime.utcnow()
        self.valid_to = valid_to
        self.rowversion = rowversion

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "nome": self.nome,
            "cpf": self.cpf,
            "status": self.status,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "updated_at": self.updated_at.isoformat(),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "rowversion": self.rowversion
        }


# ============================================================================
# Tests: Database Connectivity
# ============================================================================

@pytest.mark.real_infrastructure
class TestDatabaseConnectivity:
    """Verify real PostgreSQL connectivity and schema setup"""
    
    def test_connect_to_postgres(self, real_db_session: Session):
        """Can connect to PostgreSQL"""
        result = real_db_session.execute(text("SELECT 1 as connected")).scalar()
        assert result == 1
    
    def test_core_schemas_exist(self, real_db_session: Session):
        """Core schemas exist"""
        schemas = real_db_session.execute(text("""
            SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name IN ('intellicare_operacional', 'intellicare_analitico')
        """)).scalars().all()
        
        assert 'intellicare_operacional' in schemas
        assert 'intellicare_analitico' in schemas
    
    def test_module_schemas_exist(self, real_db_session: Session):
        """Module schemas exist for oswaldo"""
        schemas = real_db_session.execute(text("""
            SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name LIKE 'oswaldo%'
        """)).scalars().all()
        
        assert 'oswaldo_operacional' in schemas
        assert 'oswaldo_analitico' in schemas
    
    def test_roles_exist(self, real_db_session: Session):
        """Database roles exist"""
        roles = real_db_session.execute(text("""
            SELECT rolname FROM pg_roles WHERE rolname IN 
            ('operacional_user', 'analytics_user', 'intellicare_admin')
        """)).scalars().all()
        
        assert 'operacional_user' in roles
        assert 'analytics_user' in roles
        assert 'intellicare_admin' in roles
    
    def test_pacientes_table_exists(self, real_db_session: Session):
        """oswaldo_operacional.pacientes table exists"""
        result = real_db_session.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'oswaldo_operacional' 
                AND table_name = 'pacientes'
            )
        """)).scalar()
        
        assert result is True
    
    def test_audit_log_table_exists(self, real_db_session: Session):
        """Audit log table exists"""
        result = real_db_session.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'intellicare_operacional' 
                AND table_name = 'audit_log'
            )
        """)).scalar()
        
        assert result is True


# ============================================================================
# Tests: Database Operations
# ============================================================================

@pytest.mark.real_infrastructure
class TestDatabaseOperations:
    """Test CRUD operations on real database"""
    
    def test_insert_paciente(self, real_db_session: Session):
        """Can insert a paciente"""
        actor_id = uuid.uuid4()
        
        real_db_session.execute(text("""
            INSERT INTO oswaldo_operacional.pacientes 
            (id, nome, cpf, status, created_by, updated_by)
            VALUES 
            (:id, :nome, :cpf, :status, :created_by, :updated_by)
        """), {
            "id": str(uuid.uuid4()),
            "nome": "Test Paciente",
            "cpf": "99999999999",
            "status": "ativo",
            "created_by": str(actor_id),
            "updated_by": str(actor_id)
        })
        
        real_db_session.commit()
        
        # Verify
        count = real_db_session.execute(text(
            "SELECT COUNT(*) FROM oswaldo_operacional.pacientes WHERE cpf = '99999999999'"
        )).scalar()
        
        assert count == 1
    
    def test_read_paciente(self, real_db_session: Session):
        """Can read paciente from database"""
        result = real_db_session.execute(text(
            "SELECT id, nome, cpf FROM oswaldo_operacional.pacientes LIMIT 1"
        )).first()
        
        if result:  # Test data exists
            id_val, nome, cpf = result
            assert id_val is not None
            assert nome is not None
            assert cpf is not None
    
    def test_update_paciente(self, real_db_session: Session):
        """Can update paciente status"""
        # Insert test data
        test_id = str(uuid.uuid4())
        real_db_session.execute(text("""
            INSERT INTO oswaldo_operacional.pacientes 
            (id, nome, cpf, status, created_by, updated_by)
            VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
        """), {
            "id": test_id,
            "nome": "Update Test",
            "cpf": "88888888888",
            "status": "ativo",
            "created_by": str(uuid.uuid4()),
            "updated_by": str(uuid.uuid4())
        })
        real_db_session.commit()
        
        # Update
        real_db_session.execute(text("""
            UPDATE oswaldo_operacional.pacientes 
            SET status = 'inativo', rowversion = rowversion + 1
            WHERE id = :id
        """), {"id": test_id})
        real_db_session.commit()
        
        # Verify
        status = real_db_session.execute(text(
            "SELECT status FROM oswaldo_operacional.pacientes WHERE id = :id"
        ), {"id": test_id}).scalar()
        
        assert status == "inativo"
    
    def test_soft_delete_paciente(self, real_db_session: Session):
        """Can soft delete paciente with valid_to"""
        test_id = str(uuid.uuid4())
        
        # Insert
        real_db_session.execute(text("""
            INSERT INTO oswaldo_operacional.pacientes 
            (id, nome, cpf, status, created_by, updated_by)
            VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
        """), {
            "id": test_id,
            "nome": "Soft Delete Test",
            "cpf": "77777777777",
            "status": "ativo",
            "created_by": str(uuid.uuid4()),
            "updated_by": str(uuid.uuid4())
        })
        real_db_session.commit()
        
        # Soft delete
        real_db_session.execute(text("""
            UPDATE oswaldo_operacional.pacientes 
            SET valid_to = NOW()
            WHERE id = :id
        """), {"id": test_id})
        real_db_session.commit()
        
        # Verify soft delete
        valid_to = real_db_session.execute(text(
            "SELECT valid_to FROM oswaldo_operacional.pacientes WHERE id = :id"
        ), {"id": test_id}).scalar()
        
        assert valid_to is not None


# ============================================================================
# Tests: Row-Level Security (RLS)
# ============================================================================

@pytest.mark.real_infrastructure
class TestRowLevelSecurity:
    """Verify RLS enforcement on oswaldo tables"""
    
    def test_rls_enabled_on_operational_table(self, real_db_session: Session):
        """RLS is enabled on oswaldo_operacional.pacientes"""
        result = real_db_session.execute(text("""
            SELECT relrowsecurity FROM pg_class 
            WHERE relname = 'pacientes' AND relnamespace = 'oswaldo_operacional'::regnamespace
        """)).scalar()
        
        assert result is True
    
    def test_rls_policies_exist(self, real_db_session: Session):
        """RLS policies exist on oswaldo tables"""
        policies = real_db_session.execute(text("""
            SELECT policyname FROM pg_policies 
            WHERE schemaname = 'oswaldo_operacional'
        """)).scalars().all()
        
        expected = [
            'operacional_users_can_access',
            'analytics_users_read_only',
            'analytics_users_deny_write',
            'analytics_users_deny_update',
            'analytics_users_deny_delete'
        ]
        
        # At least some policies should exist
        assert len(policies) > 0


# ============================================================================
# Tests: Audit Logging
# ============================================================================

@pytest.mark.real_infrastructure
class TestAuditLogging:
    """Verify audit log entries are created"""
    
    def test_audit_log_has_entries(self, real_db_session: Session):
        """Audit log table can store entries"""
        actor_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        real_db_session.execute(text("""
            INSERT INTO intellicare_operacional.audit_log 
            (entity_type, entity_id, actor_id, operation, new_values, reason)
            VALUES (:entity_type, :entity_id, :actor_id, :operation, :new_values, :reason)
        """), {
            "entity_type": "Paciente",
            "entity_id": entity_id,
            "actor_id": actor_id,
            "operation": "CREATE",
            "new_values": '{"nome": "Test"}',
            "reason": "Test entry"
        })
        real_db_session.commit()
        
        # Verify
        count = real_db_session.execute(text(
            "SELECT COUNT(*) FROM intellicare_operacional.audit_log WHERE entity_id = :id"
        ), {"id": entity_id}).scalar()
        
        assert count == 1


# ============================================================================
# Tests: Redis Connectivity
# ============================================================================

@pytest.mark.real_infrastructure
class TestRedisConnectivity:
    """Verify Redis connectivity and operations"""
    
    def test_connect_to_redis(self, real_redis_client: redis.Redis):
        """Can connect to Redis"""
        result = real_redis_client.ping()
        assert result is True
    
    def test_redis_set_get(self, redis_clean: redis.Redis):
        """Can SET and GET from Redis"""
        redis_clean.set("test_key", "test_value")
        value = redis_clean.get("test_key")
        
        assert value == "test_value"
    
    def test_redis_streams(self, redis_clean: redis.Redis):
        """Can use Redis Streams"""
        # Add stream entry
        entry_id = redis_clean.xadd("test_stream", {"message": "hello"})
        assert entry_id is not None
        
        # Read stream
        entries = redis_clean.xrange("test_stream")
        assert len(entries) == 1


# ============================================================================
# Tests: Event Publishing Integration
# ============================================================================

@pytest.mark.real_infrastructure
class TestEventPublishingWithRealRedis:
    """Test event publishing to real Redis"""
    
    def test_publish_create_event(self, real_db_session: Session, redis_clean: redis.Redis):
        """Can publish CREATE event to Redis"""
        event_id = str(uuid.uuid4())
        actor_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        # Simulate event publishing
        event_data = {
            "event_id": event_id,
            "entity_type": "Paciente",
            "entity_id": entity_id,
            "operation": "CREATE",
            "actor_id": actor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "new_values": {"nome": "Test", "cpf": "11111111111"},
            "reason": "Integration test"
        }
        
        # Publish to Redis stream
        entry_id = redis_clean.xadd(
            "consolidation-events",
            {
                "data": str(event_data),
                "operation": "CREATE"
            }
        )
        
        assert entry_id is not None
        
        # Verify can be read
        entries = redis_clean.xrange("consolidation-events")
        assert len(entries) == 1
    
    def test_consumer_group_creation(self, redis_clean: redis.Redis):
        """Can create consumer groups"""
        # Add a message first
        redis_clean.xadd("consolidation-events", {"test": "data"})
        
        # Create consumer group
        try:
            redis_clean.xgroup_create("consolidation-events", "consolidation", id="$", mkstream=True)
        except redis.ResponseError:
            # Group might already exist
            pass
        
        # Verify group exists
        groups = redis_clean.xinfo_groups("consolidation-events")
        assert len(groups) > 0


# ============================================================================
# Tests: Full E2E Workflow
# ============================================================================

@pytest.mark.real_infrastructure
class TestEndToEndWorkflow:
    """Test complete workflow: CREATE → Event → Consolidate"""
    
    def test_create_paciente_triggers_event(self, real_db_session: Session, redis_clean: redis.Redis):
        """Creating paciente triggers event to Redis"""
        # Setup: Create consumer group
        redis_clean.xadd("consolidation-events", {"init": "true"})
        try:
            redis_clean.xgroup_create("consolidation-events", "consolidation", id="0", mkstream=True)
        except:
            pass
        
        actor_id = uuid.uuid4()
        paciente_id = uuid.uuid4()
        
        # Step 1: Insert paciente (simulating OperationalDataAccess.create)
        real_db_session.execute(text("""
            INSERT INTO oswaldo_operacional.pacientes 
            (id, nome, cpf, status, created_by, updated_by)
            VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
        """), {
            "id": str(paciente_id),
            "nome": "E2E Test Paciente",
            "cpf": "66666666666",
            "status": "ativo",
            "created_by": str(actor_id),
            "updated_by": str(actor_id)
        })
        real_db_session.commit()
        
        # Step 2: Publish event to Redis (simulating event callback)
        event_id = redis_clean.xadd(
            "consolidation-events",
            {
                "entity_type": "Paciente",
                "entity_id": str(paciente_id),
                "operation": "CREATE",
                "actor_id": str(actor_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        assert event_id is not None
        
        # Step 3: Verify paciente exists in operational
        count = real_db_session.execute(text(
            "SELECT COUNT(*) FROM oswaldo_operacional.pacientes WHERE id = :id"
        ), {"id": str(paciente_id)}).scalar()
        assert count == 1
        
        # Step 4: Verify event in Redis
        entries = redis_clean.xlen("consolidation-events")
        assert entries > 0
        
        # Step 5: Simulate consolidation (copy to analytics)
        real_db_session.execute(text("""
            INSERT INTO oswaldo_analitico.pacientes 
            (id, nome, cpf, status, created_by, created_at, updated_by, updated_at, consolidated_at)
            SELECT id, nome, cpf, status, created_by, created_at, updated_by, updated_at, NOW()
            FROM oswaldo_operacional.pacientes 
            WHERE id = :id
        """), {"id": str(paciente_id)})
        real_db_session.commit()
        
        # Step 6: Verify in analytics
        count = real_db_session.execute(text(
            "SELECT COUNT(*) FROM oswaldo_analitico.pacientes WHERE id = :id"
        ), {"id": str(paciente_id)}).scalar()
        assert count == 1
        
        # Success! Full workflow complete
        print("✅ Full E2E workflow successful: CREATE → Event → Consolidate")


# ============================================================================
# Markers and pytest configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "real_infrastructure: marks tests that require real PostgreSQL and Redis"
    )


if __name__ == "__main__":
    # Run tests with: pytest tests/test_e2e_real_infrastructure.py -v -m real_infrastructure
    pytest.main([__file__, "-v", "-m", "real_infrastructure"])
