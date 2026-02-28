"""Tests for BulkExportManager — 14 scenarios."""

import pytest
import pytest_asyncio

from intellicare_core.bulk.manager import BulkExportManager, DEFAULT_RESOURCE_TYPES
from intellicare_core.bulk.models import BulkExportStatus


@pytest.fixture
def manager() -> BulkExportManager:
    """Fresh manager per test (not the module singleton)."""
    return BulkExportManager()


# ── create_job ────────────────────────────────────────────────────────────────


def test_create_job_returns_job(manager: BulkExportManager) -> None:
    job = manager.create_job(
        request_url="http://server/fhir/$export",
        resource_types=["Patient"],
    )
    assert job.job_id is not None
    assert job.status == BulkExportStatus.ACCEPTED
    assert "Patient" in job.resource_types


def test_create_job_increments_total(manager: BulkExportManager) -> None:
    assert manager.total_jobs == 0
    manager.create_job("http://x/$export", ["Patient"])
    assert manager.total_jobs == 1


def test_create_job_custom_tenant(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"], tenant_id="clinic-42")
    assert job.tenant_id == "clinic-42"


# ── get_job ───────────────────────────────────────────────────────────────────


def test_get_job_returns_none_for_unknown(manager: BulkExportManager) -> None:
    assert manager.get_job("nonexistent") is None


def test_get_job_returns_created_job(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    retrieved = manager.get_job(job.job_id)
    assert retrieved is not None
    assert retrieved.job_id == job.job_id


# ── cancel_job ────────────────────────────────────────────────────────────────


def test_cancel_job_returns_true(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    assert manager.cancel_job(job.job_id) is True
    assert job.status == BulkExportStatus.CANCELLED


def test_cancel_completed_job_returns_false(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    job.status = BulkExportStatus.COMPLETED
    assert manager.cancel_job(job.job_id) is False


def test_cancel_unknown_job_returns_false(manager: BulkExportManager) -> None:
    assert manager.cancel_job("does-not-exist") is False


# ── get_ndjson ────────────────────────────────────────────────────────────────


def test_get_ndjson_returns_none_before_export(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    assert manager.get_ndjson(job.job_id, "Patient") is None


def test_get_ndjson_returns_none_for_unknown_job(manager: BulkExportManager) -> None:
    assert manager.get_ndjson("unknown", "Patient") is None


# ── build_manifest ────────────────────────────────────────────────────────────


def test_build_manifest_empty(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    manifest = manager.build_manifest(job, "http://server/api/v1")
    assert manifest.request == "http://x/$export"
    assert manifest.output == []


# ── run_export ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_export_no_db_completes(manager: BulkExportManager) -> None:
    """Without session_factory, export completes with empty data."""
    job = manager.create_job("http://x/$export", ["Patient", "Observation"])
    await manager.run_export(job.job_id, session_factory=None)
    assert job.status == BulkExportStatus.COMPLETED
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_run_export_no_db_manifest_has_types(manager: BulkExportManager) -> None:
    job = manager.create_job("http://x/$export", ["Patient"])
    await manager.run_export(job.job_id, session_factory=None)
    manifest = manager.build_manifest(job, "http://server/api/v1")
    types = {o.type for o in manifest.output}
    assert "Patient" in types


@pytest.mark.asyncio
async def test_run_export_unknown_job_is_noop(manager: BulkExportManager) -> None:
    """run_export with unknown job should not raise."""
    await manager.run_export("does-not-exist", session_factory=None)


# ── DEFAULT_RESOURCE_TYPES ────────────────────────────────────────────────────


def test_default_resource_types_includes_patient() -> None:
    assert "Patient" in DEFAULT_RESOURCE_TYPES


def test_default_resource_types_includes_observation() -> None:
    assert "Observation" in DEFAULT_RESOURCE_TYPES
