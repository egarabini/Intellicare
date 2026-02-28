"""Tests for CDS Hooks Feedback + Stats — 10 scenarios."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from grahame.api.routes.cds_hooks_routes import cds_router, _feedback_store


def _make_app() -> FastAPI:
    """Minimal FastAPI app — only cds_router (no grahame lifespan/DB)."""
    app = FastAPI()
    app.include_router(cds_router, prefix="/api/v1")
    return app


@pytest.fixture
def client() -> TestClient:
    """TestClient backed by minimal app."""
    return TestClient(_make_app(), raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def clear_feedback_store():
    """Reset feedback store between tests."""
    _feedback_store.clear()
    yield
    _feedback_store.clear()


# ── Feedback endpoint ──────────────────────────────────────────────────────────


def test_feedback_accepted_returns_204(client) -> None:
    payload = {
        "feedback": [
            {
                "card": "card-uuid-001",
                "outcome": "accepted",
                "outcomeTimestamp": "2026-02-22T10:00:00Z",
            }
        ]
    }
    response = client.post("/api/v1/cds-services/patient-view-alerts/feedback", json=payload)
    assert response.status_code == 204


def test_feedback_overridden_returns_204(client) -> None:
    payload = {"feedback": [{"card": "c1", "outcome": "overridden"}]}
    response = client.post("/api/v1/cds-services/patient-view-alerts/feedback", json=payload)
    assert response.status_code == 204


def test_feedback_no_action_returns_204(client) -> None:
    payload = {"feedback": [{"card": "c1", "outcome": "no-action"}]}
    response = client.post("/api/v1/cds-services/patient-view-alerts/feedback", json=payload)
    assert response.status_code == 204


def test_feedback_unknown_service_returns_404(client) -> None:
    payload = {"feedback": [{"card": "c1", "outcome": "accepted"}]}
    response = client.post("/api/v1/cds-services/nonexistent-svc/feedback", json=payload)
    assert response.status_code == 404


def test_feedback_multiple_entries_in_one_call(client) -> None:
    payload = {
        "feedback": [
            {"card": "c1", "outcome": "accepted"},
            {"card": "c2", "outcome": "overridden"},
            {"card": "c3", "outcome": "no-action"},
        ]
    }
    response = client.post("/api/v1/cds-services/order-sign-checker/feedback", json=payload)
    assert response.status_code == 204


# ── Feedback stats endpoint ────────────────────────────────────────────────────


def test_feedback_stats_returns_zero_before_any_feedback(client) -> None:
    response = client.get("/api/v1/cds-services/patient-view-alerts/feedback-stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_feedback"] == 0
    assert body["service_id"] == "patient-view-alerts"


def test_feedback_stats_counts_correctly(client) -> None:
    payload = {
        "feedback": [
            {"card": "c1", "outcome": "accepted"},
            {"card": "c2", "outcome": "accepted"},
        ]
    }
    client.post("/api/v1/cds-services/patient-view-alerts/feedback", json=payload)

    response = client.get("/api/v1/cds-services/patient-view-alerts/feedback-stats")
    body = response.json()
    assert body["total_feedback"] == 2
    assert body["outcomes"].get("accepted") == 2


def test_feedback_stats_multiple_outcomes(client) -> None:
    client.post(
        "/api/v1/cds-services/patient-view-alerts/feedback",
        json={"feedback": [{"card": "c1", "outcome": "accepted"}]},
    )
    client.post(
        "/api/v1/cds-services/patient-view-alerts/feedback",
        json={"feedback": [{"card": "c2", "outcome": "overridden"}]},
    )

    response = client.get("/api/v1/cds-services/patient-view-alerts/feedback-stats")
    body = response.json()
    assert body["outcomes"]["accepted"] == 1
    assert body["outcomes"]["overridden"] == 1
    assert body["total_feedback"] == 2


def test_feedback_stats_unknown_service_returns_404(client) -> None:
    response = client.get("/api/v1/cds-services/nonexistent/feedback-stats")
    assert response.status_code == 404


def test_feedback_stats_independent_per_service(client) -> None:
    client.post(
        "/api/v1/cds-services/patient-view-alerts/feedback",
        json={"feedback": [{"card": "c1", "outcome": "accepted"}]},
    )
    response = client.get("/api/v1/cds-services/order-sign-checker/feedback-stats")
    assert response.json()["total_feedback"] == 0
