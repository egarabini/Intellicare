from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from grahame.api.routes import ccda_routes
from grahame.api.routes.ccda_routes import router as ccda_router
from grahame.ccda.terminology import (
    map_condition_status,
    map_encounter_status,
    map_immunization_status,
    map_medication_request_status,
    map_observation_status,
    map_procedure_status,
    normalize_system,
)
from grahame.ccda.validators import ValidationResult
from grahame.models.base import Base
from grahame.models.fhir_resource import FHIRResource  # noqa: F401


FIXTURES = Path(__file__).parent / "fixtures"


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


def test_normalize_system_maps_oid_to_fhir_uri():
    assert normalize_system("2.16.840.1.113883.6.90") == "http://hl7.org/fhir/sid/icd-10"
    assert normalize_system("urn:oid:2.16.840.1.113883.6.1") == "http://loinc.org"
    assert normalize_system("2.16.840.1.113883.12.292") == "http://hl7.org/fhir/sid/cvx"
    assert normalize_system("2.16.840.1.113883.9999") == "urn:oid:2.16.840.1.113883.9999"


def test_status_mapping_rules():
    assert map_condition_status("completed") == "resolved"
    assert map_medication_request_status("suspended") == "on-hold"
    assert map_observation_status("completed") == "final"
    assert map_procedure_status("aborted") == "stopped"
    assert map_immunization_status("cancelled") == "not-done"
    assert map_encounter_status("completed") == "finished"


def test_import_applies_terminology_mappings(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def _always_valid(_self, _xml_text: str) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=[])

    monkeypatch.setattr(ccda_routes.CDAValidator, "validate", _always_valid)

    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("pv_ccda.xml", (FIXTURES / "pv_ccda.xml").read_bytes(), "application/xml")},
    )
    assert response.status_code == 200
    bundle = response.json()
    entries = [e["resource"] for e in bundle["entry"]]

    condition = next(r for r in entries if r["resourceType"] == "Condition")
    assert condition["clinicalStatus"]["coding"][0]["code"] == "active"
    assert condition["code"]["coding"][0]["system"] == "http://hl7.org/fhir/sid/icd-10"

    observation = next(r for r in entries if r["resourceType"] == "Observation")
    assert observation["status"] == "final"
    assert observation["code"]["coding"][0]["system"] == "http://loinc.org"


def test_import_maps_actcode_for_encounter(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def _always_valid(_self, _xml_text: str) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=[])

    monkeypatch.setattr(ccda_routes.CDAValidator, "validate", _always_valid)
    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("mv_ccda.xml", (FIXTURES / "mv_ccda.xml").read_bytes(), "application/xml")},
    )
    assert response.status_code == 200
    bundle = response.json()
    encounter = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Encounter")
    assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    assert encounter["status"] == "finished"
