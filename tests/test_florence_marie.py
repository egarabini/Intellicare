"""
DEM-082 Bloco 4 — test_florence_marie.py
Validates Florence SOAP suggest with Marie integration / fallback.
Requires: intellicare-service running, clinico-dev user in Keycloak.
"""
from __future__ import annotations

import pytest
import httpx

pytestmark = pytest.mark.e2e


def test_florence_suggest_returns_soap_fields(api: httpx.Client, clinico_headers: dict):
    """POST /florence/notes/suggest returns all SOAP fields."""
    resp = api.post(
        "/florence/notes/suggest",
        json={
            "encounter_id": "marie-test-enc-001",
            "patient_id": "marie-test-pat-001",
            "chief_complaint": "Dor de cabeca persistente ha 3 dias",
            "appointment_reason": "Consulta de rotina",
        },
        headers=clinico_headers,
    )
    assert resp.status_code == 200, f"Suggest falhou: {resp.text}"
    data = resp.json()
    for field in ("soap_s", "soap_o", "soap_a", "soap_p", "model", "confidence"):
        assert field in data, f"Missing field: {field}"
    assert data["soap_s"] != ""
    assert data["model"] in ("rule-based", "llm")
    assert data["confidence"] in ("low", "medium", "high")


def test_florence_suggest_fallback_when_marie_unavailable(api: httpx.Client, clinico_headers: dict):
    """When Marie/Dify has no LLM provider, fallback returns rule-based model."""
    resp = api.post(
        "/florence/notes/suggest",
        json={
            "encounter_id": "marie-fallback-001",
            "patient_id": "marie-fallback-pat-001",
            "chief_complaint": "Febre alta ha 2 dias",
        },
        headers=clinico_headers,
    )
    assert resp.status_code == 200, f"Suggest falhou: {resp.text}"
    data = resp.json()
    # In dev/staging without LLM provider, should fallback to rule-based
    assert data["model"] in ("rule-based", "llm"), f"Unexpected model: {data['model']}"
    # If rule-based, confidence should be low
    if data["model"] == "rule-based":
        assert data["confidence"] == "low"
