"""Tests for Bulk Data models — 8 scenarios."""

import pytest

from intellicare_core.bulk.models import (
    BulkExportJob,
    BulkExportManifest,
    BulkExportStatus,
    BulkOutputFile,
)


# ── BulkExportJob ──────────────────────────────────────────────────────────────


def test_job_default_status_is_accepted() -> None:
    job = BulkExportJob()
    assert job.status == BulkExportStatus.ACCEPTED


def test_job_generates_unique_ids() -> None:
    j1 = BulkExportJob()
    j2 = BulkExportJob()
    assert j1.job_id != j2.job_id


def test_job_stores_resource_types() -> None:
    job = BulkExportJob(resource_types=["Patient", "Observation"])
    assert "Patient" in job.resource_types
    assert "Observation" in job.resource_types


def test_job_default_tenant_id() -> None:
    job = BulkExportJob()
    assert job.tenant_id == "default"


def test_job_error_field_optional() -> None:
    job = BulkExportJob()
    assert job.error is None


# ── BulkExportManifest ────────────────────────────────────────────────────────


def test_manifest_defaults() -> None:
    manifest = BulkExportManifest(
        transactionTime="2026-02-22T00:00:00",
        request="https://server/fhir/$export",
    )
    assert manifest.requiresAccessToken is False
    assert manifest.output == []
    assert manifest.error == []


def test_manifest_with_output_file() -> None:
    out = BulkOutputFile(
        type="Patient",
        url="https://server/bulk-data/abc/Patient",
        count=50,
    )
    manifest = BulkExportManifest(
        transactionTime="2026-02-22T00:00:00",
        request="https://server/fhir/$export",
        output=[out],
    )
    assert len(manifest.output) == 1
    assert manifest.output[0].type == "Patient"
    assert manifest.output[0].count == 50


def test_manifest_json_serializable() -> None:
    manifest = BulkExportManifest(
        transactionTime="2026-02-22T00:00:00",
        request="https://server/fhir/$export",
    )
    json_str = manifest.model_dump_json()
    assert "transactionTime" in json_str
    assert "output" in json_str
