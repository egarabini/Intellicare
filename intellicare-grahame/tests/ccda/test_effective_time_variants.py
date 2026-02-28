from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from grahame.api.routes import ccda_routes
from grahame.api.routes.ccda_routes import router as ccda_router
from grahame.ccda.parser import CCDAParser
from grahame.ccda.validators import ValidationResult
from grahame.models.base import Base
from grahame.models.fhir_resource import FHIRResource  # noqa: F401


FIXTURE = Path(__file__).parent / "fixtures" / "effective_time_variants_ccda.xml"


@pytest_asyncio.fixture
async def api_app():
    app = FastAPI()
    app.include_router(ccda_router, prefix="/api/v1")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    yield app
    await engine.dispose()


@pytest.fixture
def client(api_app):
    with TestClient(api_app) as test_client:
        yield test_client


def test_parser_extracts_effective_time_variants():
    parser = CCDAParser()
    doc = parser.parse(FIXTURE.read_text(encoding="utf-8"))

    assert doc.conditions[0].onset == "2024-01-01T08:00:00"  # low
    assert doc.observations[0].effective == "2026-02-25T10:30:00"  # center
    assert doc.medications[0].frequency == {"value": "8", "unit": "h"}  # phase/period
    assert doc.procedures[0].performed == "2026-01-10T12:00:00"  # center
    assert doc.immunizations[0].occurrence == "2025-05-01T09:00:00"  # phase/center
    assert doc.encounters[0].period["start"] == "2026-02-25T15:00:00"  # center fallback


def test_import_supports_effective_time_variants(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def _always_valid(_self, _xml_text: str) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=[])

    monkeypatch.setattr(ccda_routes.CDAValidator, "validate", _always_valid)

    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("effective_time_variants_ccda.xml", FIXTURE.read_bytes(), "application/xml")},
    )
    assert response.status_code == 200
    bundle = response.json()
    resources = [e["resource"] for e in bundle["entry"]]

    condition = next(r for r in resources if r["resourceType"] == "Condition")
    assert condition["onsetDateTime"] == "2024-01-01T08:00:00"

    observation = next(r for r in resources if r["resourceType"] == "Observation")
    assert observation["effectiveDateTime"] == "2026-02-25T10:30:00"

    procedure = next(r for r in resources if r["resourceType"] == "Procedure")
    assert procedure["performedDateTime"] == "2026-01-10T12:00:00"

    immunization = next(r for r in resources if r["resourceType"] == "Immunization")
    assert immunization["occurrenceDateTime"] == "2025-05-01T09:00:00"

    encounter = next(r for r in resources if r["resourceType"] == "Encounter")
    assert encounter["period"]["start"] == "2026-02-25T15:00:00"
