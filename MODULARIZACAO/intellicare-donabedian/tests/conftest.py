"""
Pytest configuration and fixtures for intellicare-donabedian tests.
"""

import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Set environment variable BEFORE importing anything from donabedian
# Use a special value that will be converted to None
os.environ["DATABASE_SCHEMA"] = "NONE"

from donabedian.models import Base


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine.

    For SQLite in-memory databases, we need to use StaticPool to ensure
    all connections share the same in-memory database.
    """
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,  # Use StaticPool for in-memory SQLite
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    original_db_url = settings.intellicare_database_url
    settings.intellicare_database_url = TEST_DATABASE_URL
    yield settings
    settings.intellicare_database_url = original_db_url


@pytest.fixture
async def client(db_session: AsyncSession):
    """Create test HTTP client."""
    from httpx import AsyncClient
    from donabedian.api.main import create_app
    from donabedian.api.dependencies import get_db

    app = create_app()

    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Test data fixtures

@pytest.fixture
def pillar_data() -> dict:
    """Sample pillar data."""
    return {
        "name": "Eficácia",
        "description": "Capacidade de produzir melhorias na saúde",
        "display_order": 1,
    }


@pytest.fixture
def indicator_data() -> dict:
    """Sample indicator data."""
    return {
        "name": "Taxa de Ocupação",
        "description": "Percentual de leitos ocupados",
        "formula": "(leitos ocupados / total de leitos) * 100",
        "unit": "%",
        "triad_dimension": "structure",
        "target_value": 85.0,
        "target_operator": ">=",
    }


@pytest.fixture
async def sample_pillar(db_session: AsyncSession):
    """Create sample pillar in database."""
    from donabedian.models.pillar import Pillar

    pillar = Pillar(
        name="Eficácia",
        description="Capacidade de produzir melhorias na saúde",
        display_order=1,
    )
    db_session.add(pillar)
    await db_session.commit()
    await db_session.refresh(pillar)
    return pillar


@pytest.fixture
async def sample_indicator(db_session: AsyncSession):
    """Create sample indicator in database."""
    from donabedian.models.indicator import Indicator, TriadDimension

    indicator = Indicator(
        name="Taxa de Ocupação",
        description="Percentual de leitos ocupados",
        formula="(leitos ocupados / total de leitos) * 100",
        unit="%",
        triad_dimension=TriadDimension.STRUCTURE,
        target_value=85.0,
        target_operator=">=",
    )
    db_session.add(indicator)
    await db_session.commit()
    await db_session.refresh(indicator)
    return indicator


@pytest.fixture
async def sample_indicator_pillar(db_session: AsyncSession, sample_pillar, sample_indicator):
    """Create sample indicator-pillar association."""
    from donabedian.models.indicator_pillar import IndicatorPillar

    assoc = IndicatorPillar(
        indicator_id=sample_indicator.id,
        pillar_id=sample_pillar.id,
        weight=1.0,
    )
    db_session.add(assoc)
    await db_session.commit()
    await db_session.refresh(assoc)
    return assoc


@pytest.fixture
async def sample_measurement(db_session: AsyncSession, sample_indicator):
    """Create sample measurement in database."""
    from donabedian.models.measurement import Measurement, MeasurementStatus, PeriodType
    from datetime import date, timedelta

    measurement = Measurement(
        indicator_id=sample_indicator.id,
        period_start=date.today() - timedelta(days=30),
        period_end=date.today(),
        period_type=PeriodType.MONTHLY,
        value=87.5,
        status=MeasurementStatus.GREEN,
    )
    db_session.add(measurement)
    await db_session.commit()
    await db_session.refresh(measurement)
    return measurement

