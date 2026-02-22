"""
============================================================================
NISE TRAINING MODULE - TEST CONFIGURATION
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Pytest Configuration and Fixtures
Versão: 1.0
Data: 20/03/2026
Responsável: DEV2
============================================================================
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.models import Patient, Observation, Practitioner, Encounter

# ============================================================================
# TEST DATABASE CONFIGURATION
# ============================================================================

# Use in-memory SQLite for tests (or a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/nise_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    
    This fixture:
    1. Creates all tables before the test
    2. Yields a database session
    3. Rolls back any changes after the test
    4. Drops all tables after the test
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing.
    
    This fixture:
    1. Overrides the get_db dependency to use the test database
    2. Creates an AsyncClient
    3. Yields the client for testing
    4. Closes the client after the test
    """
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def sample_patient(db_session: AsyncSession) -> Patient:
    """Create a sample patient for testing."""
    patient_data = {
        "resourceType": "Patient",
        "id": "test-patient-123",
        "name": [{"family": "Test", "given": ["Patient"]}],
        "gender": "male",
        "birthDate": "1990-01-01"
    }
    
    patient = Patient(
        fhir_id="test-patient-123",
        fhir_resource=patient_data
    )
    
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    
    return patient


@pytest.fixture(scope="function")
async def sample_practitioner(db_session: AsyncSession) -> Practitioner:
    """Create a sample practitioner for testing."""
    practitioner_data = {
        "resourceType": "Practitioner",
        "id": "test-practitioner-123",
        "name": [{"family": "Test", "given": ["Doctor"]}]
    }
    
    practitioner = Practitioner(
        fhir_id="test-practitioner-123",
        fhir_resource=practitioner_data
    )
    
    db_session.add(practitioner)
    await db_session.commit()
    await db_session.refresh(practitioner)
    
    return practitioner


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an async test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )

