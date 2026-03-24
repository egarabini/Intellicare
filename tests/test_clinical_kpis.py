"""
DEM-082 Bloco 4 — test_clinical_kpis.py
Validates clinical KPIs endpoint (DEM-081).
Requires: intellicare-service running, gestor-dev user in Keycloak.
"""
from __future__ import annotations

import pytest
import httpx

pytestmark = pytest.mark.e2e


def test_clinical_kpis_returns_structure(api: httpx.Client, gestor_headers: dict):
    """GET /admin/kpis/clinical returns expected KPI structure."""
    resp = api.get(
        "/admin/kpis/clinical",
        params={"start": "2026-01-01", "end": "2026-12-31"},
        headers=gestor_headers,
    )
    assert resp.status_code == 200, f"KPIs failed: {resp.text}"
    data = resp.json()
    for field in ("encounters", "notes", "prescriptions", "interactions_detected"):
        assert field in data, f"Missing field: {field}"
    assert isinstance(data["encounters"], int)
    assert isinstance(data["prescriptions"], int)


def test_clinical_kpis_requires_auth(api: httpx.Client):
    """KPIs endpoint requires authentication."""
    resp = api.get(
        "/admin/kpis/clinical",
        params={"start": "2026-01-01", "end": "2026-12-31"},
    )
    assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
