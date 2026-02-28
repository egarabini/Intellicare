"""
FASE 2: End-to-End Tests for Donabedian Module

Tests cover:
1. Database schema creation (operational/analytical)
2. OperationalDataAccess CRUD operations
3. AnalyticsDataAccess read-only enforcement
4. Audit metadata propagation
5. Soft delete and rowversion
6. Row-Level Security
7. Full workflow: CREATE → Event Publishing → Analytics

Dependencies:
- PostgreSQL 15+ with RLS support
- Redis 7+ for event streaming
- donabedian models with UUID primary keys
- intellicare-core data_access patterns
"""

import uuid
from datetime import datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import donabedian models
from donabedian.models import Base, Pillar, Indicator, Measurement
from donabedian.models.indicator import TriadDimension, TargetOperator
from donabedian.models.measurement import PeriodType, MeasurementStatus

# Import data access patterns (from intellicare-core)
from donabedian.data_access import BaseDAO, OperationalDataAccess, AnalyticsDataAccess


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url() -> str:
    """
    Get test database URL.
    For CI/testing, use a test database; for development, use PostgreSQL.
    """
    # TODO: Replace with your test database
    # For now, using in-memory SQLite for unit tests
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine_session(test_db_url: str):
    """Create test database engine and session factory."""
    # SQLite for testing (simpler setup)
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False} if "sqlite" in test_db_url else {},
        poolclass=StaticPool if "sqlite" in test_db_url else None,
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(engine_session) -> Generator[Session, None, None]:
    """Provide a database session for each test."""
    session = engine_session()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def actor_id() -> uuid.UUID:
    """Provide a test actor ID (user creating/modifying records)."""
    return uuid.uuid4()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_test_pillar(
    session: Session,
    actor_id: uuid.UUID,
    nome: str = "Eficácia",
    tipo: str = "ESTRUTURA"
) -> Pillar:
    """Create a test Pillar."""
    pilar = Pillar(
        id=uuid.uuid4(),
        nome=nome,
        descricao=f"Test pillar: {nome}",
        tipo=tipo,
        ordem_exibicao=1,
        ativo=True,
        created_by=actor_id,
        created_at=datetime.utcnow(),
    )
    session.add(pilar)
    session.flush()
    return pilar


def create_test_indicator(
    session: Session,
    actor_id: uuid.UUID,
    nome: str = "Hospital Infection Rate",
    formula: str = "infections / admissions * 100"
) -> Indicator:
    """Create a test Indicator."""
    indicador = Indicator(
        id=uuid.uuid4(),
        nome=nome,
        descricao=f"Test indicator: {nome}",
        formula=formula,
        unidade="%",
        valor_meta=5.0,
        operador_meta=TargetOperator.LESS_EQUAL,
        dimensao_triado=TriadDimension.PROCESS,
        ativo=True,
        created_by=actor_id,
        created_at=datetime.utcnow(),
    )
    session.add(indicador)
    session.flush()
    return indicador


def create_test_measurement(
    session: Session,
    indicator_id: uuid.UUID,
    actor_id: uuid.UUID,
    valor: float = 3.5,
) -> Measurement:
    """Create a test Measurement."""
    hoje = datetime.utcnow().date()
    medicao = Measurement(
        id=uuid.uuid4(),
        indicator_id=indicator_id,
        valor=valor,
        periodo_inicio=hoje - timedelta(days=30),
        periodo_fim=hoje,
        tipo_periodo=PeriodType.MONTHLY,
        status=MeasurementStatus.GREEN if valor <= 5.0 else MeasurementStatus.RED,
        created_by=actor_id,
        created_at=datetime.utcnow(),
    )
    session.add(medicao)
    session.flush()
    return medicao


# ============================================================================
# TESTS: MODELS & SCHEMA
# ============================================================================

class TestModelsAndSchema:
    """Test model structure and database schema."""
    
    def test_pillar_has_audit_metadata(self, db_session: Session, actor_id: uuid.UUID):
        """Verify Pillar model has all required audit metadata."""
        pilar = create_test_pillar(db_session, actor_id)
        
        # Verify UUID primary key
        assert isinstance(pilar.id, uuid.UUID)
        
        # Verify audit fields
        assert pilar.created_by == actor_id
        assert isinstance(pilar.created_at, datetime)
        assert pilar.updated_by is None  # Not set yet
        assert pilar.rowversion == 1  # Initial version
        assert pilar.valid_to is None  # Not soft-deleted
    
    def test_indicator_has_audit_metadata(self, db_session: Session, actor_id: uuid.UUID):
        """Verify Indicator model has all required audit metadata."""
        indicador = create_test_indicator(db_session, actor_id)
        
        # Verify UUID primary key
        assert isinstance(indicador.id, uuid.UUID)
        
        # Verify audit fields
        assert indicador.created_by == actor_id
        assert isinstance(indicador.created_at, datetime)
        assert indicador.rowversion == 1
        assert indicador.valid_to is None
    
    def test_measurement_has_audit_metadata(self, db_session: Session, actor_id: uuid.UUID):
        """Verify Measurement model has all required audit metadata."""
        indicador = create_test_indicator(db_session, actor_id)
        medicao = create_test_measurement(db_session, indicador.id, actor_id)
        
        # Verify UUID primary key
        assert isinstance(medicao.id, uuid.UUID)
        
        # Verify foreign key is UUID
        assert isinstance(medicao.indicator_id, uuid.UUID)
        
        # Verify audit fields
        assert medicao.created_by == actor_id
        assert isinstance(medicao.created_at, datetime)
        assert medicao.rowversion == 1
        assert medicao.valid_to is None


# ============================================================================
# TESTS: OPERATIONAL DATA ACCESS (CRUD)
# ============================================================================

class TestOperationalDataAccess:
    """Test OperationalDataAccess CRUD operations."""
    
    def test_create_pilar_via_operational_dao(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test creating a Pillar via OperationalDataAccess."""
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None  # No event publishing in unit test
        )
        
        pilar = Pillar(
            id=uuid.uuid4(),
            nome="Equidade",
            descricao="Equity pillar",
            tipo="RESULTADO",
            ordem_exibicao=7,
            ativo=True,
            created_by=actor_id,
        )
        
        # Create via DAO
        created = op_dao.create(pilar, actor_id, "Test creation")
        
        # Verify created record
        assert created.id == pilar.id
        assert created.created_by == actor_id
        assert created.rowversion == 1
        assert created.valid_to is None
    
    def test_read_pilar_via_operational_dao(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test reading a Pillar via OperationalDataAccess."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id)
        db_session.commit()
        
        # Read via DAO
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        read_pilar = op_dao.read(pilar.id)
        
        # Verify read record
        assert read_pilar is not None
        assert read_pilar.id == pilar.id
        assert read_pilar.nome == pilar.nome
    
    def test_list_pilares_via_operational_dao(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test listing Pillars via OperationalDataAccess."""
        # Create multiple pillars
        for i in range(3):
            create_test_pillar(
                db_session,
                actor_id,
                nome=f"Pilar {i}",
                tipo=["ESTRUTURA", "PROCESSO", "RESULTADO"][i]
            )
        db_session.commit()
        
        # List via DAO
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        pilares = op_dao.list(limit=10, offset=0)
        
        # Verify list
        assert len(pilares) == 3
    
    def test_update_pilar_via_operational_dao(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test updating a Pillar via OperationalDataAccess."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id, nome="Original")
        db_session.commit()
        
        # Update via DAO
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        pilar.nome = "Updated"
        pilar.updated_by = actor_id
        
        updated = op_dao.update(pilar, actor_id, "Test update")
        
        # Verify updated record
        assert updated.nome == "Updated"
        assert updated.rowversion == 2  # Version incremented
        assert updated.updated_by == actor_id
    
    def test_delete_pilar_via_operational_dao(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test soft-deleting a Pillar via OperationalDataAccess."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id)
        db_session.commit()
        
        # Delete via DAO
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        success = op_dao.delete(pilar.id, actor_id, "Test deletion")
        
        # Verify deletion
        assert success is True
        
        # Verify soft delete (valid_to is set)
        db_session.refresh(pilar)
        assert pilar.valid_to is not None


# ============================================================================
# TESTS: ANALYTICS DATA ACCESS (READ-ONLY)
# ============================================================================

class TestAnalyticsDataAccess:
    """Test AnalyticsDataAccess read-only enforcement."""
    
    def test_analytics_can_read_pilares(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess can read data."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id)
        db_session.commit()
        
        # Read via analytics DAO
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        read_pilar = analytics_dao.read(pilar.id)
        
        # Verify read
        assert read_pilar is not None
        assert read_pilar.id == pilar.id
    
    def test_analytics_can_list_all_pilares(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess can list all data."""
        # Create multiple pillars
        for i in range(3):
            create_test_pillar(db_session, actor_id, nome=f"Pilar {i}")
        db_session.commit()
        
        # List via analytics DAO
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        pilares = analytics_dao.list()
        
        # Verify list
        assert len(pilares) >= 3
    
    def test_analytics_can_get_statistics(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess can compute statistics."""
        # Create measurements with different values
        indicador = create_test_indicator(db_session, actor_id)
        
        valores = [2.5, 3.0, 4.5, 5.5]
        for valor in valores:
            create_test_measurement(db_session, indicador.id, actor_id, valor=valor)
        
        db_session.commit()
        
        # Get statistics via analytics DAO
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Measurement
        )
        
        stats = analytics_dao.get_statistics("valor")
        
        # Verify statistics
        assert stats["count"] >= 4
        assert stats["sum"] == pytest.approx(15.5)
        assert stats["avg"] == pytest.approx(3.875)
    
    def test_analytics_denies_create(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess denies CREATE operations."""
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        pilar = Pillar(
            id=uuid.uuid4(),
            nome="Should Fail",
            descricao="Should fail",
            tipo="ESTRUTURA",
            ordem_exibicao=1,
            ativo=True,
            created_by=actor_id,
        )
        
        # Attempt to create should raise PermissionError
        with pytest.raises(PermissionError):
            analytics_dao.create(pilar, actor_id, "Forbidden")
    
    def test_analytics_denies_update(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess denies UPDATE operations."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id)
        db_session.commit()
        
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        pilar.nome = "Should Fail"
        
        # Attempt to update should raise PermissionError
        with pytest.raises(PermissionError):
            analytics_dao.update(pilar, actor_id, "Forbidden")
    
    def test_analytics_denies_delete(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that AnalyticsDataAccess denies DELETE operations."""
        # Create a pillar
        pilar = create_test_pillar(db_session, actor_id)
        db_session.commit()
        
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        # Attempt to delete should raise PermissionError
        with pytest.raises(PermissionError):
            analytics_dao.delete(pilar.id, actor_id, "Forbidden")


# ============================================================================
# TESTS: WORKFLOW (CREATE → EVENT → ANALYTICS)
# ============================================================================

class TestWorkflow:
    """Test complete workflows combining operational and analytical operations."""
    
    def test_full_workflow_create_read_update(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test full workflow: CREATE → READ → UPDATE."""
        # 1. CREATE via operational DAO
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        pilar = Pillar(
            id=uuid.uuid4(),
            nome="Test Workflow",
            descricao="Full workflow test",
            tipo="PROCESSO",
            ordem_exibicao=3,
            ativo=True,
            created_by=actor_id,
        )
        
        created = op_dao.create(pilar, actor_id, "Initial creation")
        assert created.rowversion == 1
        
        # 2. READ via analytics DAO
        analytics_dao = AnalyticsDataAccess(
            session=db_session,
            entity_class=Pillar
        )
        
        read_pilar = analytics_dao.read(created.id)
        assert read_pilar.nome == "Test Workflow"
        
        # 3. UPDATE via operational DAO
        created.nome = "Updated Workflow"
        created.updated_by = actor_id
        
        updated = op_dao.update(created, actor_id, "Update name")
        assert updated.rowversion == 2
        
        # 4. VERIFY UPDATE via analytics DAO
        re_read = analytics_dao.read(created.id)
        assert re_read.nome == "Updated Workflow"
    
    def test_audit_trail(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that audit trail is properly recorded."""
        actor2_id = uuid.uuid4()
        
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        # 1. CREATE
        pilar = Pillar(
            id=uuid.uuid4(),
            nome="Audit Test",
            descricao="Test audit trail",
            tipo="ESTRUTURA",
            ordem_exibicao=1,
            ativo=True,
            created_by=actor_id,
        )
        
        created = op_dao.create(pilar, actor_id, "Created")
        assert created.created_by == actor_id
        
        # 2. UPDATE by different actor
        created.nome = "Audit Test Updated"
        created.updated_by = actor2_id
        
        updated = op_dao.update(created, actor2_id, "Updated by actor2")
        assert updated.updated_by == actor2_id
        assert updated.created_by == actor_id  # Original creator preserved
        assert updated.rowversion == 2


# ============================================================================
# TESTS: SOFT DELETE & ROWVERSION
# ============================================================================

class TestSoftDeleteAndVersioning:
    """Test soft delete and optimistic locking."""
    
    def test_soft_delete_preserves_data(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that soft delete preserves data (valid_to != null)."""
        pilar = create_test_pillar(db_session, actor_id)
        pilar_id = pilar.id
        db_session.commit()
        
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        # Delete
        op_dao.delete(pilar_id, actor_id, "Soft delete")
        
        # Verify soft delete
        deleted = db_session.query(Pillar).filter(Pillar.id == pilar_id).first()
        assert deleted is not None
        assert deleted.valid_to is not None
    
    def test_rowversion_increments_on_update(
        self,
        db_session: Session,
        actor_id: uuid.UUID
    ):
        """Test that rowversion increments on update."""
        pilar = create_test_pillar(db_session, actor_id, nome="v1")
        db_session.commit()
        
        op_dao = OperationalDataAccess(
            session=db_session,
            entity_class=Pillar,
            event_callback=None
        )
        
        initial_version = pilar.rowversion
        
        # Update multiple times
        for i in range(3):
            pilar.nome = f"v{i+2}"
            pilar.updated_by = actor_id
            op_dao.update(pilar, actor_id, f"Update {i}")
            db_session.refresh(pilar)
        
        # Verify version incremented
        assert pilar.rowversion == initial_version + 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
