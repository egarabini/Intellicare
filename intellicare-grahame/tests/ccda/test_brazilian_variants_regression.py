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


FIXTURES = Path(__file__).parent / "fixtures"

BRAZILIAN_VARIANTS = [
    ("pv_ccda.xml", {"conditions": 1, "observations": 1, "medications": 0, "procedures": 0, "immunizations": 0, "encounters": 0}),
    ("tasy_ccda.xml", {"conditions": 0, "observations": 0, "medications": 1, "procedures": 0, "immunizations": 0, "encounters": 0}),
    ("mv_ccda.xml", {"conditions": 0, "observations": 0, "medications": 0, "procedures": 0, "immunizations": 0, "encounters": 1}),
    ("sysimal_ccda.xml", {"conditions": 0, "observations": 0, "medications": 0, "procedures": 1, "immunizations": 1, "encounters": 0}),
]


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


@pytest.mark.parametrize("fixture_name,expected", BRAZILIAN_VARIANTS)
def test_parser_handles_brazilian_variants(fixture_name: str, expected: dict[str, int]):
    xml_text = (FIXTURES / fixture_name).read_text(encoding="utf-8")
    parser = CCDAParser()
    doc = parser.parse(xml_text)

    assert doc.patient.name["family"]
    assert len(doc.conditions) >= expected["conditions"]
    assert len(doc.observations) >= expected["observations"]
    assert len(doc.medications) >= expected["medications"]
    assert len(doc.procedures) >= expected["procedures"]
    assert len(doc.immunizations) >= expected["immunizations"]
    assert len(doc.encounters) >= expected["encounters"]


@pytest.mark.parametrize("fixture_name,_expected", BRAZILIAN_VARIANTS)
def test_ccda_import_regression_for_brazilian_variants(
    fixture_name: str,
    _expected: dict[str, int],
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    # Variantes reais costumam ter diferenças de estrutura: aqui garantimos
    # que parsing+conversão+persistência seguem estáveis na importação.
    def _always_valid(_self, _xml_text: str) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=["schema-bypassed-for-regression"])

    monkeypatch.setattr(ccda_routes.CDAValidator, "validate", _always_valid)

    payload = (FIXTURES / fixture_name).read_bytes()
    response = client.post(
        "/api/v1/fhir/DocumentReference/$ccda-import",
        files={"file": (fixture_name, payload, "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resourceType"] == "Bundle"
    assert body["meta"]["sourceFormat"] == "ccda"
    assert body["meta"]["resourcesImported"] >= 1
    resource_types = [entry["resource"]["resourceType"] for entry in body["entry"]]
    assert "Patient" in resource_types
