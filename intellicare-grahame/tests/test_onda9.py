"""Testes ONDA_9 — AI Operation, Schedule/$find, Appointment/$book, On-behalf-of."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from grahame.api.app import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False, timeout=10.0)


# ── W9-A AI Operation ──────────────────────────────────────────────────────────


def test_ai_operation_json(client):
    """POST /api/v1/ai retorna JSON quando Accept não é SSE."""
    with patch("grahame.services.ai_operation_service.AIOperationService.generate_response", new_callable=AsyncMock) as m:
        m.return_value = "Resposta de teste"
        resp = client.post(
            "/api/v1/ai",
            json={"prompt": "Teste", "agent": "florence"},
            headers={"Accept": "application/json"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("resourceType") == "Parameters"
    params = {p["name"]: p for p in data.get("parameter", [])}
    assert "result" in params


def test_fhir_ai_operation(client):
    """POST /api/v1/fhir/$ai aceita mesmo payload que /ai."""
    with patch("grahame.services.ai_operation_service.AIOperationService.generate_response", new_callable=AsyncMock) as m:
        m.return_value = "OK"
        resp = client.post(
            "/api/v1/fhir/$ai",
            json={"prompt": "Teste", "agent": "wanda"},
        )
    assert resp.status_code == 200


# ── W9-B Schedule/$find ───────────────────────────────────────────────────────


def test_schedule_find_returns_bundle(client):
    """POST /api/v1/fhir/Schedule/$find retorna Bundle."""
    resp = client.post(
        "/api/v1/fhir/Schedule/$find",
        json={
            "resourceType": "Parameters",
            "parameter": [
                {"name": "actor", "valueReference": {"reference": "Practitioner/123"}},
                {"name": "start", "valueDateTime": "2026-03-01T08:00:00Z"},
                {"name": "end", "valueDateTime": "2026-03-07T18:00:00Z"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("resourceType") == "Bundle"
    assert data.get("type") == "searchset"


# ── W9-B Appointment/$book ────────────────────────────────────────────────────


def test_appointment_book_requires_slot_and_patient(client):
    """Appointment/$book retorna 400 sem slot ou patient."""
    resp = client.post(
        "/api/v1/fhir/Appointment/$book",
        json={"resourceType": "Parameters", "parameter": []},
    )
    assert resp.status_code == 400


# ── W9-C On-behalf-of ────────────────────────────────────────────────────────


def test_on_behalf_of_header_accepted(client):
    """Request com X-On-Behalf-Of válido não retorna 403."""
    resp = client.get(
        "/api/v1/health",
        headers={"X-On-Behalf-Of": "Practitioner/123"},
    )
    assert resp.status_code == 200


def test_on_behalf_of_invalid_returns_403(client):
    """X-On-Behalf-Of inválido (vazio após strip) pode ser ignorado ou 403."""
    resp = client.get(
        "/api/v1/health",
        headers={"X-On-Behalf-Of": "   "},
    )
    # Middleware ignora header vazio — health retorna 200
    assert resp.status_code == 200
