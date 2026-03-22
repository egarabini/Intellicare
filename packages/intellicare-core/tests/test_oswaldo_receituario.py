import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from modules.oswaldo.services import format_posologia, generate_receituario, detect_route
from intellicare_core.contracts.base import TenantContext

def test_format_posologia_normal():
    item = {"posology": "1 comp 8/8h", "duration": "5 dias"}
    res = format_posologia(item)
    assert "1 (um)" in res
    assert "a cada 8" in res
    assert "5 (cinco) dias" in res
    assert res.startswith("Tomar")
    assert res.endswith(".")

def test_format_posologia_already_formatted():
    item = {"posology": "Tomar 1 comp", "duration": ""}
    res = format_posologia(item)
    assert res.startswith("Tomar")
    assert "1 (um)" in res
    assert res.endswith(".")


def test_format_posologia_frequency_expansion():
    item = {"posology": "2 comp 12/12h", "duration": "7 dias"}
    res = format_posologia(item)
    assert "2 (dois)" in res
    assert "a cada 12 horas" in res
    assert "7 (sete) dias" in res


def test_detect_route_comp():
    assert detect_route("1 comp 8/8h") == "Via Oral"


def test_detect_route_pomada():
    assert detect_route("aplicar pomada 2x/dia") == "Uso Tópico"


@pytest.mark.asyncio
@patch("modules.oswaldo.repository.get_prescription")
@patch("modules.oswaldo.repository.get_professional_by_keycloak_id")
@patch("modules.oswaldo.repository.get_patient_by_id")
@patch("modules.oswaldo.services.render_pdf")
@patch("modules.oswaldo.services.generate_qr_base64")
async def test_generate_receituario(mock_qr, mock_render, mock_patient, mock_prof, mock_rx):
    # Cria objeto mock para simular o banco
    rx_mock = MagicMock()
    rx_mock.id = 123
    rx_mock.patient_id = "1"
    rx_mock.items = []
    rx_mock.created_at = datetime.datetime.now()
    rx_mock.cid10_code = "A00"
    rx_mock.cid10_desc = "Colera"
    
    mock_rx.return_value = rx_mock
    mock_prof.return_value = {"name": "Dr. Test", "crm_number": "123", "crm_state": "SP"}
    mock_patient.return_value = {"name": "Paciente Test", "cpf": "111"}
    
    mock_qr.return_value = "base64"
    mock_render.return_value = b"PDF_BYTES"

    ctx = TenantContext.from_slug(slug="tenant_test", user_id="user_1")
    object.__setattr__(ctx, "roles", ["CLINICO"])
    res = await generate_receituario(ctx, 123, "simple")

    assert res == b"PDF_BYTES"
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    assert args[0] == "receituario.html"
    
    # Valida Contexto do Template
    context = args[1]
    assert "data" in context
    assert context["data"].prescription_type == "simple"
    assert context["data"].professional_name == "Dr. Test"


@pytest.mark.asyncio
@patch("modules.oswaldo.repository.get_prescription")
@patch("modules.oswaldo.repository.get_professional_by_keycloak_id")
@patch("modules.oswaldo.repository.get_patient_by_id")
@patch("modules.oswaldo.services.render_pdf")
@patch("modules.oswaldo.services.generate_qr_base64")
async def test_generate_receituario_special_control(mock_qr, mock_render, mock_patient, mock_prof, mock_rx):
    rx_mock = MagicMock()
    rx_mock.id = 42
    rx_mock.patient_id = "1"
    rx_mock.items = []
    rx_mock.created_at = datetime.datetime.now()
    rx_mock.cid10_code = "F10"
    rx_mock.cid10_desc = "Dependencia"

    mock_rx.return_value = rx_mock
    mock_prof.return_value = {"name": "Dr. Z", "crm_number": "999", "crm_state": "RJ", "specialty": "Psiquiatria"}
    mock_patient.return_value = {"name": "Paciente SC", "cpf": "123.456.789-00"}
    mock_qr.return_value = "qrbase64"
    mock_render.return_value = b"PDF"

    ctx = TenantContext.from_slug(slug="tenant_test", user_id="user_2")
    object.__setattr__(ctx, "roles", ["CLINICO"])
    res = await generate_receituario(ctx, 42, "special_control")

    assert res == b"PDF"
    context = mock_render.call_args[0][1]
    data = context["data"]
    assert data.prescription_type == "special_control"
    assert data.prescription_validity_days == 30
    assert data.prescription_number == "NT-000042"
    assert data.patient_cpf == "123.456.789-00"
