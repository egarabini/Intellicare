from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from grahame.api.routes.ccda_routes import router as ccda_router
from grahame.models.base import Base
from grahame.models.fhir_resource import FHIRResource  # noqa: F401


VALID_FIXTURE = Path(__file__).parent / "fixtures" / "sample_ccda_valid.xml"
INVALID_FIXTURE = Path(__file__).parent / "fixtures" / "sample_ccda.xml"
INVALID_SCHEMA_XML = b'<?xml version="1.0" encoding="UTF-8"?><ClinicalDocument xmlns="urn:hl7-org:v3"></ClinicalDocument>'


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


def test_ccda_import_returns_bundle(client):
    payload = VALID_FIXTURE.read_bytes()

    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("sample_ccda_valid.xml", payload, "application/xml")},
    )
    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["meta"]["sourceFormat"] == "ccda"
    assert bundle["meta"]["resourcesImported"] >= 1

    types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
    assert "Patient" in types


def test_ccda_import_invalid_xml_returns_operation_outcome(client):
    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("invalid.xml", b"<ClinicalDocument>", "application/xml")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["resourceType"] == "OperationOutcome"


def test_ccda_import_invalid_schema_returns_operation_outcome(client):
    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": ("sample_ccda_invalid_schema.xml", INVALID_SCHEMA_XML, "application/xml")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["resourceType"] == "OperationOutcome"


def test_ccda_validate_endpoint(client):
    response = client.post(
        "/api/v1/ccda/validate",
        files={"file": ("sample_ccda_valid.xml", VALID_FIXTURE.read_bytes(), "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert "errors" in body
    assert "Schema validation skipped" not in body.get("warnings", [])


def test_ccda_validate_invalid_schema(client):
    response = client.post(
        "/api/v1/ccda/validate",
        files={"file": ("sample_ccda_invalid_schema.xml", INVALID_SCHEMA_XML, "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"]
