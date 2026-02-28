"""Fixtures para testes do intellicare-grahame."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from grahame.models.base import Base
from grahame.models.codesystem_concept import CodeSystemConcept  # noqa: F401 — registra tabela no metadata
from grahame.models.fhir_resource import FHIRResource
from grahame.api.app import app
from grahame.api.dependencies.hl7v2_auth import get_db_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

PATIENT_SILVA = {
    "resourceType": "Patient",
    "id": "patient-123",
    "active": True,
    "name": [{"family": "Silva", "given": ["João"]}],
    "gender": "male",
    "birthDate": "1980-01-01",
}

PATIENT_SANTOS = {
    "resourceType": "Patient",
    "id": "patient-456",
    "active": True,
    "name": [{"family": "Santos", "given": ["Maria"]}],
    "gender": "female",
    "birthDate": "1990-05-15",
}

OBSERVATION_HEARTRATE = {
    "resourceType": "Observation",
    "id": "obs-001",
    "status": "final",
    "code": {
        "coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]
    },
    "subject": {"reference": "Patient/patient-123"},
    "valueQuantity": {"value": 80, "unit": "beats/minute"},
}


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture(scope="function")
async def db_session(session: AsyncSession):
    """Backward-compatible alias used by HL7v2 audit endpoint tests."""
    yield session


@pytest.fixture(scope="function")
def client(db_session: AsyncSession):
    """TestClient with DB dependency overridden to use the test session."""

    async def _override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest_asyncio.fixture
async def patient_silva(session: AsyncSession) -> FHIRResource:
    row = FHIRResource(
        resource_type="Patient",
        fhir_id="patient-123",
        resource=PATIENT_SILVA,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


@pytest_asyncio.fixture
async def observation_heartrate(session: AsyncSession, patient_silva) -> FHIRResource:
    row = FHIRResource(
        resource_type="Observation",
        fhir_id="obs-001",
        resource=OBSERVATION_HEARTRATE,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
