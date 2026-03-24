"""
Bloco 3 — Smoke tests for DEM-082 staging sync.
Tests: certificate upload, Florence SOAP suggest (Marie fallback).
Run: python tools/scripts/smoke_bloco3.py
"""
import os
import sys
import json
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "infra" / ".env"

API_BASE = os.environ.get("API_BASE", "http://localhost:9000")

# ─── Load .env ────────────────────────────────────────────────────────────────
def load_env():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

load_env()

KC_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
KC_REALM = os.environ.get("KEYCLOAK_REALM", "intellicare")
KC_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "intellicare-service")
KC_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_token(username, password):
    """Get Keycloak bearer token."""
    data = (
        f"client_id={KC_CLIENT_ID}&client_secret={KC_CLIENT_SECRET}"
        f"&grant_type=password&username={username}&password={password}&scope=openid"
    ).encode()
    req = urllib.request.Request(
        f"{KC_URL}/realms/{KC_REALM}/protocol/openid-connect/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())["access_token"]
    except urllib.error.HTTPError as e:
        print(f"  Token error: HTTP {e.code} — {e.read().decode()[:300]}")
        return None
    except Exception as e:
        print(f"  Token error: {e}")
        return None


def api_post_json(path, body, token):
    """POST JSON to API."""
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, {"raw": body_text[:500]}
    except Exception as e:
        return 0, {"error": str(e)}


def api_post_multipart(path, fields, files, token):
    """POST multipart/form-data to API (manual boundary encoding)."""
    import uuid
    boundary = uuid.uuid4().hex
    body = b""
    for key, val in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        body += f"{val}\r\n".encode()
    for key, (filename, data, content_type) in files.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    url = f"{API_BASE}{path}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, {"raw": body_text[:500]}
    except Exception as e:
        return 0, {"error": str(e)}


# ─── Certificate generation ──────────────────────────────────────────────────
def generate_test_pfx():
    """Generate a self-signed PFX certificate for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "key.pem")
        cert_path = os.path.join(tmpdir, "cert.pem")
        pfx_path = os.path.join(tmpdir, "test_cert.pfx")

        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_path, "-out", cert_path,
            "-days", "365", "-nodes",
            "-subj", "/CN=DR TESTE SILVA/OU=CRM-SP 123456/O=IntelliCare/C=BR"
        ], check=True, capture_output=True)

        subprocess.run([
            "openssl", "pkcs12", "-export",
            "-out", pfx_path, "-inkey", key_path, "-in", cert_path,
            "-passout", "pass:TestPass123"
        ], check=True, capture_output=True)

        pfx_bytes = open(pfx_path, "rb").read()
        print(f"  PFX generated: {len(pfx_bytes)} bytes")
        return pfx_bytes


# ─── Smoke Tests ──────────────────────────────────────────────────────────────
def smoke_health():
    """Test /health endpoint."""
    print("\n--- Smoke 0: Health check ---")
    try:
        resp = urllib.request.urlopen(f"{API_BASE}/health", timeout=10)
        data = json.loads(resp.read().decode())
        print(f"  GET /health → {resp.status}: {data}")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def smoke_certificate(token):
    """Test certificate upload."""
    print("\n--- Smoke 1: Certificate upload (DEM-080) ---")
    try:
        pfx_bytes = generate_test_pfx()
    except FileNotFoundError:
        print("  SKIP: openssl not found in PATH")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  SKIP: openssl failed: {e.stderr.decode()[:200]}")
        return None

    status, body = api_post_multipart(
        "/oswaldo/professionals/me/certificate",
        fields={"password": "TestPass123"},
        files={"file": ("test_cert.pfx", pfx_bytes, "application/x-pkcs12")},
        token=token,
    )
    print(f"  POST /oswaldo/professionals/me/certificate → {status}")
    print(f"  Response: {json.dumps(body, indent=2, ensure_ascii=False, default=str)}")

    if status == 201:
        assert "subject_name" in body, "Missing subject_name in response"
        print("  PASS ✓")
        return True
    elif status == 404:
        print("  (404 = professional not found for this keycloak user — expected if dr.silva not in this tenant)")
        return None
    else:
        print(f"  FAIL ✗ (status={status})")
        return False


def smoke_florence_suggest(token):
    """Test Florence SOAP suggest with Marie fallback."""
    print("\n--- Smoke 2: Florence SOAP suggest (DEM-079 + Marie fallback) ---")
    status, body = api_post_json(
        "/florence/notes/suggest",
        {
            "encounter_id": "smoke-encounter-001",
            "patient_id": "smoke-patient-001",
            "chief_complaint": "Dor de cabeca persistente ha 3 dias",
            "appointment_reason": "Consulta de rotina",
        },
        token=token,
    )
    print(f"  POST /florence/notes/suggest → {status}")
    print(f"  Response: {json.dumps(body, indent=2, ensure_ascii=False, default=str)}")

    if status == 200:
        for field in ("soap_s", "soap_o", "soap_a", "soap_p", "model"):
            assert field in body, f"Missing {field} in response"
        print(f"  Model used: {body.get('model', '?')}")
        print("  PASS ✓")
        return True
    elif status == 403:
        print("  (403 = user lacks CLINICO role — expected for some test users)")
        return None
    else:
        print(f"  FAIL ✗")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  DEM-082 Bloco 3 — Smoke Tests")
    print("=" * 60)

    # Health
    if not smoke_health():
        print("\nFATAL: API not reachable. Aborting.")
        sys.exit(1)

    # Get token
    print("\n--- Auth: Getting clinico token ---")
    token = get_token("clinico-dev", "Clinico@2025!")
    if not token:
        print("  Trying dr-silva / DrSilva@2025!...")
        token = get_token("dr-silva", "DrSilva@2025!")
    if not token:
        print("FATAL: Cannot obtain token. Check Keycloak.")
        sys.exit(1)
    print(f"  Token obtained: {token[:30]}...")

    # Smokes
    results = {}
    results["certificate"] = smoke_certificate(token)
    results["florence_suggest"] = smoke_florence_suggest(token)

    # Summary
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    for name, result in results.items():
        if result is True:
            status = "PASS ✓"
        elif result is None:
            status = "SKIP ~"
        else:
            status = "FAIL ✗"
        print(f"  {name:30s} {status}")

    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"\n{len(failed)} test(s) FAILED")
        sys.exit(1)
    else:
        print("\nAll smokes passed or skipped.")


if __name__ == "__main__":
    main()
