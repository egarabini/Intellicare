"""E2E — DEM-027: Endpoints de Relatórios PDF."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e


def test_admin_report_tenants_returns_pdf(api: httpx.Client, admin_headers: dict):
    """GET /reports/admin/tenants retorna application/pdf."""
    resp = api.get("/reports/admin/tenants", headers=admin_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content[:4] == b"%PDF"


def test_gestor_report_appointments_returns_pdf(api: httpx.Client, gestor_headers: dict):
    """GET /reports/gestor/appointments retorna application/pdf."""
    resp = api.get("/reports/gestor/appointments", headers=gestor_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content[:4] == b"%PDF"


def test_clinico_report_patients_returns_pdf(api: httpx.Client, clinico_headers: dict):
    """GET /reports/clinico/patients retorna application/pdf."""
    resp = api.get("/reports/clinico/patients", headers=clinico_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content[:4] == b"%PDF"


def test_report_unauthenticated_returns_401(api: httpx.Client):
    """GET /reports/admin/tenants sem token retorna 401."""
    resp = api.get("/reports/admin/tenants")
    assert resp.status_code == 401


def test_report_wrong_role_returns_403(api: httpx.Client, gestor_headers: dict):
    """GET /reports/admin/tenants com token de gestor retorna 403."""
    resp = api.get("/reports/admin/tenants", headers=gestor_headers)
    assert resp.status_code == 403
