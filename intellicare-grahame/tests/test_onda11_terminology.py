"""W11-B/W11-C regression tests for terminology operations and i18n."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from grahame.api.app import app
from grahame.services.display_resolver import resolve_display
from grahame.utils.accept_language import parse_accept_language


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_accept_language_parser_orders_by_q():
    langs = parse_accept_language("pt-BR, pt;q=0.9, en;q=0.8")
    assert langs[:3] == ["pt-BR", "pt", "en"]


def test_display_resolver_prefers_pt_br():
    display = resolve_display(
        default_display="Diabetes mellitus type 2",
        designations={"pt-BR": "Diabetes mellitus tipo 2", "es": "Diabetes tipo 2"},
        languages=["pt-BR", "en"],
    )
    assert display == "Diabetes mellitus tipo 2"


def test_codesystem_lookup_post_with_accept_language(client: TestClient):
    fake_result = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "name", "valueString": "ICD-10"},
            {"name": "display", "valueString": "Diabetes mellitus type 2"},
            {
                "name": "designation",
                "part": [
                    {"name": "language", "valueCode": "pt-BR"},
                    {"name": "value", "valueString": "Diabetes mellitus tipo 2"},
                ],
            },
        ],
    }
    with patch("grahame.api.routes.terminology_routes.lookup", return_value=fake_result):
        resp = client.post(
            "/api/v1/fhir/CodeSystem/$lookup",
            headers={"Accept-Language": "pt-BR, en;q=0.8"},
            json={
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "system", "valueUri": "http://hl7.org/fhir/sid/icd-10"},
                    {"name": "code", "valueCode": "E11"},
                ],
            },
        )
    assert resp.status_code == 200
    params = resp.json()["parameter"]
    display = next(p for p in params if p.get("name") == "display")
    assert display["valueString"] == "Diabetes mellitus tipo 2"


def test_codesystem_validate_code_post(client: TestClient):
    fake_lookup = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "display", "valueString": "Heart rate"},
        ],
    }
    with patch("grahame.api.routes.terminology_routes.lookup", return_value=fake_lookup):
        resp = client.post(
            "/api/v1/fhir/CodeSystem/$validate-code",
            json={"system": "http://loinc.org", "code": "8867-4"},
        )
    assert resp.status_code == 200
    params = resp.json()["parameter"]
    assert any(p.get("name") == "result" and p.get("valueBoolean") is True for p in params)
    assert any(p.get("name") == "display" for p in params)


def test_valueset_validate_code_post(client: TestClient):
    fake_result = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            {"name": "display", "valueString": "Body temperature"},
        ],
    }
    with patch("grahame.api.routes.terminology_routes.validate_code", return_value=fake_result):
        resp = client.post(
            "/api/v1/fhir/ValueSet/$validate-code",
            json={"url": "http://x/vs", "system": "http://loinc.org", "code": "8310-5"},
        )
    assert resp.status_code == 200
    assert any(p.get("name") == "result" and p.get("valueBoolean") is True for p in resp.json()["parameter"])
