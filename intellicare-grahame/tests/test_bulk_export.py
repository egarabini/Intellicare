"""Tests for FHIR Bulk Data $export routes — 13 scenarios."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import intellicare_core.bulk.manager as _m
from grahame.api.routes.bulk_export_routes import bulk_router
from intellicare_core.bulk.manager import BulkExportManager
from intellicare_core.bulk.models import BulkExportStatus


def _make_app(manager: BulkExportManager) -> FastAPI:
    """Minimal FastAPI app — only bulk_router (no grahame lifespan/DB)."""
    _m._manager = manager
    app = FastAPI()
    app.include_router(bulk_router, prefix="/api/v1")
    return app


@pytest.fixture
def manager() -> BulkExportManager:
    """Fresh BulkExportManager per test; run_export patched to no-op so jobs stay ACCEPTED."""
    fresh = BulkExportManager()

    async def _noop(job_id: str, session_factory=None) -> None:
        pass  # prevent background task from auto-completing jobs in tests

    fresh.run_export = _noop  # type: ignore[method-assign]
    _m._manager = fresh
    yield fresh
    _m._manager = None


@pytest.fixture
def client(manager: BulkExportManager) -> TestClient:
    """TestClient backed by minimal app (no grahame lifespan)."""
    app = _make_app(manager)
    return TestClient(app, raise_server_exceptions=True)


# ── System kick-off ─────────────────────────────────────────────────────────────


def test_system_export_returns_202(client, manager) -> None:
    response = client.get("/api/v1/$export")
    assert response.status_code == 202


def test_system_export_has_content_location(client, manager) -> None:
    response = client.get("/api/v1/$export")
    assert "content-location" in response.headers
    assert "bulk-status" in response.headers["content-location"]


def test_system_export_with_type_filter(client, manager) -> None:
    response = client.get("/api/v1/$export?_type=Patient,Observation")
    assert response.status_code == 202
    job_id = response.headers["content-location"].split("/")[-1]
    job = manager.get_job(job_id)
    assert job is not None
    assert "Patient" in job.resource_types
    assert "Observation" in job.resource_types


# ── Patient kick-off ────────────────────────────────────────────────────────────


def test_patient_export_returns_202(client, manager) -> None:
    response = client.get("/api/v1/Patient/$export")
    assert response.status_code == 202


def test_patient_export_only_patient_types(client, manager) -> None:
    response = client.get("/api/v1/Patient/$export?_type=Patient,DiagnosticReport")
    assert response.status_code == 202
    job_id = response.headers["content-location"].split("/")[-1]
    job = manager.get_job(job_id)
    # DiagnosticReport is not in patient compartment — filtered out
    assert "DiagnosticReport" not in job.resource_types
    assert "Patient" in job.resource_types


# ── Status polling ──────────────────────────────────────────────────────────────


def test_status_returns_202_while_in_progress(client, manager) -> None:
    response = client.get("/api/v1/$export")
    job_id = response.headers["content-location"].split("/")[-1]
    job = manager.get_job(job_id)
    job.status = BulkExportStatus.IN_PROGRESS
    status_resp = client.get(f"/api/v1/bulk-status/{job_id}")
    assert status_resp.status_code == 202
    assert status_resp.headers.get("x-progress") == "in-progress"


def test_status_returns_200_when_completed(client, manager) -> None:
    from datetime import UTC, datetime

    response = client.get("/api/v1/$export")
    job_id = response.headers["content-location"].split("/")[-1]
    job = manager.get_job(job_id)
    job.status = BulkExportStatus.COMPLETED
    job.completed_at = datetime.now(UTC)
    status_resp = client.get(f"/api/v1/bulk-status/{job_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert "transactionTime" in body
    assert "output" in body


def test_status_returns_404_for_unknown_job(client, manager) -> None:
    response = client.get("/api/v1/bulk-status/nonexistent-job")
    assert response.status_code == 404


# ── Cancel ──────────────────────────────────────────────────────────────────────


def test_cancel_returns_202(client, manager) -> None:
    response = client.get("/api/v1/$export")
    job_id = response.headers["content-location"].split("/")[-1]
    cancel_resp = client.delete(f"/api/v1/bulk-status/{job_id}")
    assert cancel_resp.status_code == 202


def test_cancel_nonexistent_job_returns_404(client, manager) -> None:
    response = client.delete("/api/v1/bulk-status/does-not-exist")
    assert response.status_code == 404


# ── Download NDJSON ─────────────────────────────────────────────────────────────


def test_download_completed_job_returns_ndjson(client, manager) -> None:
    import json
    from datetime import UTC, datetime

    response = client.get("/api/v1/$export?_type=Patient")
    job_id = response.headers["content-location"].split("/")[-1]

    job = manager.get_job(job_id)
    manager._data[job_id]["Patient"] = [
        json.dumps({"resourceType": "Patient", "id": "p1"}),
    ]
    job.status = BulkExportStatus.COMPLETED
    job.completed_at = datetime.now(UTC)

    dl_resp = client.get(f"/api/v1/bulk-data/{job_id}/Patient")
    assert dl_resp.status_code == 200
    assert "application/fhir+ndjson" in dl_resp.headers["content-type"]
    assert "Patient" in dl_resp.text


def test_download_not_completed_returns_404(client, manager) -> None:
    response = client.get("/api/v1/$export?_type=Patient")
    job_id = response.headers["content-location"].split("/")[-1]
    # Job still in ACCEPTED state → 404
    dl_resp = client.get(f"/api/v1/bulk-data/{job_id}/Patient")
    assert dl_resp.status_code == 404


def test_download_unknown_type_returns_404(client, manager) -> None:
    from datetime import UTC, datetime

    response = client.get("/api/v1/$export?_type=Patient")
    job_id = response.headers["content-location"].split("/")[-1]
    job = manager.get_job(job_id)
    job.status = BulkExportStatus.COMPLETED
    job.completed_at = datetime.now(UTC)
    # Observation was not requested — 404
    dl_resp = client.get(f"/api/v1/bulk-data/{job_id}/Observation")
    assert dl_resp.status_code == 404
