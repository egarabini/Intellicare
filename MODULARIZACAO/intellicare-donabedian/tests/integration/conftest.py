"""
Fixtures para testes de integração.
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from donabedian.api.main import app
from donabedian.models import Base
from donabedian.api.dependencies import get_db


# Database URL para testes de integração (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session):
    """Create a test client with database override."""
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_pillar(test_session):
    """Create a sample pillar for testing."""
    from donabedian.models.pillar import Pillar
    
    pillar = Pillar(
        name="Eficácia",
        description="Capacidade de produzir o efeito desejado",
        display_order=1
    )
    test_session.add(pillar)
    await test_session.commit()
    await test_session.refresh(pillar)
    return pillar


@pytest.fixture
async def sample_indicator(test_session):
    """Create a sample indicator for testing."""
    from donabedian.models.indicator import Indicator
    from donabedian.models.indicator import TriadDimension
    
    indicator = Indicator(
        name="Taxa de Ocupação",
        description="Percentual de leitos ocupados",
        formula="(leitos_ocupados / total_leitos) * 100",
        unit="%",
        target_value=85.0,
        target_operator="<=",
        triad_dimension=TriadDimension.STRUCTURE
    )
    test_session.add(indicator)
    await test_session.commit()
    await test_session.refresh(indicator)
    return indicator


@pytest.fixture
async def sample_measurement(test_session, sample_indicator):
    """Create a sample measurement for testing."""
    from donabedian.models.measurement import Measurement, PeriodType
    from datetime import datetime
    
    measurement = Measurement(
        indicator_id=sample_indicator.id,
        value=82.5,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 1, 31),
        period_type=PeriodType.MONTHLY
    )
    test_session.add(measurement)
    await test_session.commit()
    await test_session.refresh(measurement)
    return measurement


@pytest.fixture
async def sample_indicator_pillar(test_session, sample_indicator, sample_pillar):
    """Create a sample indicator-pillar association for testing."""
    from donabedian.models.indicator_pillar import IndicatorPillar
    
    association = IndicatorPillar(
        indicator_id=sample_indicator.id,
        pillar_id=sample_pillar.id,
        weight=1.0
    )
    test_session.add(association)
    await test_session.commit()
    await test_session.refresh(association)
    return association

