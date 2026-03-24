"""
DEM-082 Bloco 4 — test_assinatura_digital.py
Validates digital certificate upload (DEM-080).
Requires: intellicare-service running, clinico-dev user with professionals record.
"""
from __future__ import annotations

import subprocess
import tempfile
import os

import pytest
import httpx

pytestmark = pytest.mark.e2e


def _generate_test_pfx() -> bytes:
    """Generate a self-signed PFX for testing via openssl."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "key.pem")
        cert_path = os.path.join(tmpdir, "cert.pem")
        pfx_path = os.path.join(tmpdir, "test.pfx")

        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", key_path, "-out", cert_path,
                "-days", "365", "-nodes",
                "-subj", "/CN=DR TESTE PYTEST/OU=CRM-SP 999999/O=IntelliCare/C=BR",
            ],
            check=True, capture_output=True,
        )
        subprocess.run(
            [
                "openssl", "pkcs12", "-export",
                "-out", pfx_path, "-inkey", key_path, "-in", cert_path,
                "-passout", "pass:TestPass123",
            ],
            check=True, capture_output=True,
        )
        return open(pfx_path, "rb").read()


@pytest.fixture(scope="module")
def pfx_bytes():
    try:
        return _generate_test_pfx()
    except FileNotFoundError:
        pytest.skip("openssl not found in PATH")


def test_certificate_upload(api: httpx.Client, clinico_headers: dict, pfx_bytes: bytes):
    """POST /oswaldo/professionals/me/certificate uploads and returns cert info."""
    resp = api.post(
        "/oswaldo/professionals/me/certificate",
        files={"file": ("test.pfx", pfx_bytes, "application/x-pkcs12")},
        data={"password": "TestPass123"},
        headers=clinico_headers,
    )
    # 201 = uploaded, 404 = no professional record (acceptable in some envs)
    if resp.status_code == 404:
        pytest.skip("Professional record not found for clinico-dev")
    assert resp.status_code == 201, f"Upload failed: {resp.text}"
    data = resp.json()
    assert "subject_name" in data
    assert "valid_until" in data
    assert "uploaded_at" in data


def test_certificate_status_after_upload(api: httpx.Client, clinico_headers: dict):
    """GET /oswaldo/professionals/me/certificate returns status."""
    resp = api.get(
        "/oswaldo/professionals/me/certificate",
        headers=clinico_headers,
    )
    if resp.status_code == 404:
        pytest.skip("No professional record")
    assert resp.status_code == 200, f"Status check failed: {resp.text}"
    data = resp.json()
    assert "has_certificate" in data


def test_upload_rejects_non_pfx(api: httpx.Client, clinico_headers: dict):
    """Upload of non-.pfx file should be rejected with 400."""
    resp = api.post(
        "/oswaldo/professionals/me/certificate",
        files={"file": ("not_a_cert.txt", b"not a certificate", "text/plain")},
        data={"password": "whatever"},
        headers=clinico_headers,
    )
    assert resp.status_code == 400, f"Expected 400 for non-PFX, got {resp.status_code}"
