"""Testes para DEM-080 — Assinatura Digital Receituário."""
import datetime
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
PFX_PATH = FIXTURES / "test_cert.pfx"
PFX_PASSWORD = "TestPass123"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_pfx() -> bytes:
    assert PFX_PATH.exists(), f"Fixture não encontrada: {PFX_PATH}"
    return PFX_PATH.read_bytes()


def _make_ctx(**overrides):
    ctx = MagicMock()
    ctx.tenant_id = overrides.get("tenant_id", "clinica_alfa")
    ctx.schema = overrides.get("schema", "tenant_clinica_alfa")
    ctx.user_id = overrides.get("user_id", "kc-uid-123")
    ctx.email = overrides.get("email", "dr.silva@demo.intellicare")
    ctx.roles = overrides.get("roles", ["CLINICO"])
    ctx.has_role = lambda r: r in ctx.roles
    return ctx


# ── Test 1: upload encrypts the cert ────────────────────────────────────────

def test_upload_certificate_stores_encrypted():
    """Upload .pfx → armazenado criptografado, não como texto plano."""
    os.environ.setdefault("SERVER_ENCRYPTION_KEY", "2kFw8mZv0nqhPJ6EJ1nE96x-eY1J5C0S0f3u5yWqN5M=")

    from intellicare_core.crypto import encrypt_bytes, decrypt_bytes

    pfx_bytes = _load_pfx()
    encrypted = encrypt_bytes(pfx_bytes)

    # Criptografado não é igual ao original
    assert encrypted != pfx_bytes
    assert len(encrypted) > len(pfx_bytes)

    # Descriptografar retorna original
    decrypted = decrypt_bytes(encrypted)
    assert decrypted == pfx_bytes


# ── Test 2: extract_certificate_info works ──────────────────────────────────

def test_extract_certificate_info():
    """Extrai subject_name e valid_until do .pfx de teste."""
    from modules.oswaldo.pdf_signer import extract_certificate_info

    pfx_bytes = _load_pfx()
    info = extract_certificate_info(pfx_bytes, PFX_PASSWORD)

    assert "subject_name" in info
    assert "valid_until" in info
    assert "DR TESTE SILVA" in info["subject_name"]
    assert isinstance(info["valid_until"], datetime.date)


# ── Test 3: extract with wrong password raises ──────────────────────────────

def test_extract_certificate_wrong_password():
    """Senha errada → ValueError ou exceção."""
    from modules.oswaldo.pdf_signer import extract_certificate_info

    pfx_bytes = _load_pfx()
    with pytest.raises(Exception):
        extract_certificate_info(pfx_bytes, "wrong_password")


# ── Test 4: sign_pdf produces signed output ─────────────────────────────────

def test_sign_pdf_produces_signed_output():
    """PDF assinado é maior que o original e começa com %PDF."""
    from modules.oswaldo.pdf_signer import sign_pdf

    # Gerar um PDF mínimo
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string="<html><body><h1>Teste</h1></body></html>").write_pdf()
    except (ImportError, OSError):
        pytest.skip("weasyprint não disponível neste ambiente")

    pfx_bytes = _load_pfx()
    signed = sign_pdf(pdf_bytes, pfx_bytes, PFX_PASSWORD)

    assert signed[:4] == b"%PDF"
    assert len(signed) > len(pdf_bytes)


# ── Test 5: sign_pdf rejects wrong password ─────────────────────────────────

def test_sign_pdf_wrong_password():
    """Senha errada no sign_pdf → exceção."""
    from modules.oswaldo.pdf_signer import sign_pdf

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string="<html><body><h1>Teste</h1></body></html>").write_pdf()
    except (ImportError, OSError):
        pytest.skip("weasyprint não disponível neste ambiente")

    pfx_bytes = _load_pfx()
    with pytest.raises(Exception):
        sign_pdf(pdf_bytes, pfx_bytes, "wrong_password")


# ── Test 6: generate_receituario without certificate works ──────────────────

@pytest.mark.asyncio
@patch("modules.oswaldo.repository.get_prescription")
@patch("modules.oswaldo.repository.get_professional_by_keycloak_id")
@patch("modules.oswaldo.repository.get_patient_by_id")
@patch("modules.oswaldo.repository.get_professional_certificate")
@patch("modules.oswaldo.services.render_pdf")
@patch("modules.oswaldo.services.generate_qr_base64")
async def test_receituario_unsigned_when_no_certificate(
    mock_qr, mock_render, mock_cert, mock_patient, mock_prof, mock_rx
):
    """Médico sem cert → PDF retornado sem assinatura, sem erro."""
    from modules.oswaldo.services import generate_receituario

    rx_mock = MagicMock()
    rx_mock.id = 1
    rx_mock.patient_id = "1"
    rx_mock.items = []
    rx_mock.created_at = datetime.datetime.now()
    rx_mock.cid10_code = "A00"
    rx_mock.cid10_desc = "Colera"

    mock_rx.return_value = rx_mock
    mock_prof.return_value = {"id": 1, "name": "Dr. Test", "crm_number": "123", "crm_state": "SP"}
    mock_patient.return_value = {"name": "Paciente Test", "cpf": "111"}
    mock_cert.return_value = None  # sem certificado
    mock_qr.return_value = "base64"
    mock_render.return_value = b"%PDF-fake"

    ctx = _make_ctx()
    result = await generate_receituario(ctx, 1, "simple")

    assert result == b"%PDF-fake"
    mock_cert.assert_called_once_with(ctx, 1)


# ── Test 7: generate_receituario with certificate calls sign ────────────────

@pytest.mark.asyncio
@patch("modules.oswaldo.repository.get_prescription")
@patch("modules.oswaldo.repository.get_professional_by_keycloak_id")
@patch("modules.oswaldo.repository.get_patient_by_id")
@patch("modules.oswaldo.repository.get_professional_certificate")
@patch("modules.oswaldo.services.render_pdf")
@patch("modules.oswaldo.services.generate_qr_base64")
async def test_receituario_signed_when_certificate_exists(
    mock_qr, mock_render, mock_cert, mock_patient, mock_prof, mock_rx
):
    """Médico com cert → sign_pdf é chamado."""
    os.environ.setdefault("SERVER_ENCRYPTION_KEY", "2kFw8mZv0nqhPJ6EJ1nE96x-eY1J5C0S0f3u5yWqN5M=")

    from modules.oswaldo.services import generate_receituario
    from intellicare_core.crypto import encrypt_bytes, encrypt_text

    pfx_bytes = _load_pfx()

    rx_mock = MagicMock()
    rx_mock.id = 2
    rx_mock.patient_id = "1"
    rx_mock.items = []
    rx_mock.created_at = datetime.datetime.now()
    rx_mock.cid10_code = "A00"
    rx_mock.cid10_desc = "Colera"

    mock_rx.return_value = rx_mock
    mock_prof.return_value = {"id": 1, "name": "Dr. Test", "crm_number": "123", "crm_state": "SP"}
    mock_patient.return_value = {"name": "Paciente Test", "cpf": "111"}
    mock_cert.return_value = {
        "pfx_encrypted": encrypt_bytes(pfx_bytes),
        "password_hash": encrypt_text(PFX_PASSWORD),
    }
    mock_qr.return_value = "base64"

    try:
        from weasyprint import HTML
        real_pdf = HTML(string="<html><body><h1>Teste</h1></body></html>").write_pdf()
        mock_render.return_value = real_pdf
    except (ImportError, OSError):
        pytest.skip("weasyprint não disponível neste ambiente")

    ctx = _make_ctx()
    result = await generate_receituario(ctx, 2, "simple")

    assert result[:4] == b"%PDF"
    assert len(result) > len(real_pdf)  # assinatura aumenta o tamanho
    mock_cert.assert_called_once()


# ── Test 8: delete certificate returns to unsigned ──────────────────────────

@pytest.mark.asyncio
@patch("modules.oswaldo.repository.get_prescription")
@patch("modules.oswaldo.repository.get_professional_by_keycloak_id")
@patch("modules.oswaldo.repository.get_patient_by_id")
@patch("modules.oswaldo.repository.get_professional_certificate")
@patch("modules.oswaldo.services.render_pdf")
@patch("modules.oswaldo.services.generate_qr_base64")
async def test_delete_certificate_removes_signature(
    mock_qr, mock_render, mock_cert, mock_patient, mock_prof, mock_rx
):
    """Após DELETE → próximo receituário sem assinatura."""
    from modules.oswaldo.services import generate_receituario

    rx_mock = MagicMock()
    rx_mock.id = 3
    rx_mock.patient_id = "1"
    rx_mock.items = []
    rx_mock.created_at = datetime.datetime.now()
    rx_mock.cid10_code = "A00"
    rx_mock.cid10_desc = "Colera"

    mock_rx.return_value = rx_mock
    mock_prof.return_value = {"id": 1, "name": "Dr. Test", "crm_number": "123", "crm_state": "SP"}
    mock_patient.return_value = {"name": "Paciente Test", "cpf": "111"}
    mock_cert.return_value = None  # certificado foi removido
    mock_qr.return_value = "base64"
    mock_render.return_value = b"%PDF-unsigned"

    ctx = _make_ctx()
    result = await generate_receituario(ctx, 3, "simple")

    # PDF retornado sem assinatura (idêntico ao render_pdf)
    assert result == b"%PDF-unsigned"
