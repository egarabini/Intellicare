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


FIXTURE = Path(__file__).parent / "fixtures" / "entry_relationship_complex_ccda.xml"


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


def test_parser_handles_complex_entry_relationships():
    parser = CCDAParser()
    doc = parser.parse(FIXTURE.read_text(encoding="utf-8"))

    assert len(doc.conditions) >= 1
    cond = doc.conditions[0]
    assert cond.code["code"] == "I50.9"
    assert cond.status == "completed"
    assert cond.onset == "2023-01-01T10:00:00"

    assert len(doc.observations) >= 1
    obs = doc.observations[0]
    assert obs.code["code"] == "4548-4"
    assert obs.value["value"] == "7.1"
    assert obs.effective == "2026-02-25T10:10:10"

    assert len(doc.medications) >= 1
    med = doc.medications[0]
    assert med.medication_code["code"] == "861004"
    assert med.status == "suspended"
    assert med.frequency == {"value": "24", "unit": "h"}


def test_import_handles_complex_entry_relationships(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def _always_valid(_self, _xml_text: str) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=[])

    monkeypatch.setattr(ccda_routes.CDAValidator, "validate", _always_valid)

    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("entry_relationship_complex_ccda.xml", FIXTURE.read_bytes(), "application/xml")},
    )
    assert response.status_code == 200
    bundle = response.json()
    resources = [e["resource"] for e in bundle["entry"]]

    condition = next(r for r in resources if r["resourceType"] == "Condition")
    assert condition["code"]["coding"][0]["code"] == "I50.9"
    assert condition["clinicalStatus"]["coding"][0]["code"] == "resolved"

    observation = next(r for r in resources if r["resourceType"] == "Observation")
    assert observation["code"]["coding"][0]["code"] == "4548-4"
    assert observation["valueQuantity"]["value"] == 7.1

    medication = next(r for r in resources if r["resourceType"] == "MedicationRequest")
    assert medication["medicationCodeableConcept"]["coding"][0]["code"] == "861004"
    assert medication["status"] == "on-hold"
