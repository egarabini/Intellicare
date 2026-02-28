"""Regression tests for W10-B ConceptMap import and $translate."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from grahame.api.app import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _conceptmap_payload() -> dict:
    return {
        "resourceType": "ConceptMap",
        "id": "cm-icd-snomed",
        "url": "http://example.org/fhir/ConceptMap/icd-snomed",
        "group": [
            {
                "source": "http://hl7.org/fhir/sid/icd-10",
                "target": "http://snomed.info/sct",
                "element": [
                    {
                        "code": "E11",
                        "display": "Type 2 diabetes mellitus",
                        "target": [
                            {
                                "code": "44054006",
                                "display": "Diabetes mellitus type 2",
                                "equivalence": "equivalent",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_conceptmap_import_bundle_and_translate_match(client: TestClient):
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": _conceptmap_payload()}],
    }
    import_resp = client.post(
        "/api/v1/fhir/ConceptMap/$import",
        headers={"X-Tenant-ID": "tenant-cm"},
        json=bundle,
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["imported"] == 1

    translate_resp = client.post(
        "/api/v1/fhir/ConceptMap/$translate",
        headers={"X-Tenant-ID": "tenant-cm"},
        json={
            "resourceType": "Parameters",
            "parameter": [
                {"name": "url", "valueUri": "http://example.org/fhir/ConceptMap/icd-snomed"},
                {"name": "system", "valueUri": "http://hl7.org/fhir/sid/icd-10"},
                {"name": "code", "valueCode": "E11"},
                {"name": "target", "valueUri": "http://snomed.info/sct"},
            ],
        },
    )
    assert translate_resp.status_code == 200
    data = translate_resp.json()
    params = data.get("parameter", [])
    assert any(p.get("name") == "result" and p.get("valueBoolean") is True for p in params)
    assert any(p.get("name") == "match" for p in params)


def test_conceptmap_translate_no_match(client: TestClient):
    client.post(
        "/api/v1/fhir/ConceptMap/$import",
        headers={"X-Tenant-ID": "tenant-cm-nomatch"},
        json=_conceptmap_payload(),
    )

    resp = client.post(
        "/api/v1/fhir/ConceptMap/$translate",
        headers={"X-Tenant-ID": "tenant-cm-nomatch"},
        json={"code": "X99", "system": "http://hl7.org/fhir/sid/icd-10"},
    )
    assert resp.status_code == 200
    params = resp.json().get("parameter", [])
    assert any(p.get("name") == "result" and p.get("valueBoolean") is False for p in params)


def test_conceptmap_translate_reverse(client: TestClient):
    client.post(
        "/api/v1/fhir/ConceptMap/$import",
        headers={"X-Tenant-ID": "tenant-cm-reverse"},
        json=_conceptmap_payload(),
    )

    resp = client.post(
        "/api/v1/fhir/ConceptMap/$translate",
        headers={"X-Tenant-ID": "tenant-cm-reverse"},
        json={
            "code": "44054006",
            "system": "http://snomed.info/sct",
            "reverse": True,
            "target": "http://hl7.org/fhir/sid/icd-10",
        },
    )
    assert resp.status_code == 200
    matches = [p for p in resp.json().get("parameter", []) if p.get("name") == "match"]
    assert matches, resp.text


def test_conceptmap_translate_by_id(client: TestClient):
    payload = _conceptmap_payload()
    client.post(
        "/api/v1/fhir/ConceptMap/$import",
        headers={"X-Tenant-ID": "tenant-cm-id"},
        json=payload,
    )
    resp = client.post(
        "/api/v1/fhir/ConceptMap/cm-icd-snomed/$translate",
        headers={"X-Tenant-ID": "tenant-cm-id"},
        json={"code": "E11", "system": "http://hl7.org/fhir/sid/icd-10"},
    )
    assert resp.status_code == 200
    assert any(
        p.get("name") == "result" and p.get("valueBoolean") is True
        for p in resp.json().get("parameter", [])
    )
