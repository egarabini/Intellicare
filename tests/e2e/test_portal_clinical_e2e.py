"""DEM-063 — Portal clínico E2E: jornadas, notas sem soap_a, isolamento de role."""
from __future__ import annotations

import pytest
import httpx

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def paciente_headers() -> dict[str, str]:
    """Token do paciente.alfa (tenant_alfa)."""
    from .conftest import get_token, auth_headers
    return auth_headers(get_token("paciente.alfa", "Demo@1234"))


def test_patient_sees_journeys(api: httpx.Client, paciente_headers: dict):
    """Paciente pode listar suas jornadas via /cuidado/paciente/me/journeys."""
    resp = api.get(
        "/cuidado/paciente/me/journeys",
        headers=paciente_headers,
    )
    assert resp.status_code == 200, f"Journeys falhou: {resp.text}"
    data = resp.json()
    assert isinstance(data, list)


def test_patient_notes_no_soap_a(api: httpx.Client, paciente_headers: dict):
    """Notas clínicas do paciente não expõem campo soap_a."""
    resp = api.get(
        "/cuidado/paciente/me/clinical-notes",
        headers=paciente_headers,
    )
    assert resp.status_code == 200, f"Clinical notes falhou: {resp.text}"
    data = resp.json()
    assert isinstance(data, list)
    # PacienteClinicalNoteItem não tem soap_a — verificar que nunca aparece
    for note in data:
        assert "soap_a" not in note, "soap_a não deve ser exposto ao paciente"
        assert "soap_s" not in note, "soap_s não deve ser exposto ao paciente"


def test_clinical_role_cannot_access_patient_portal(
    api: httpx.Client, clinico_headers: dict,
):
    """Clínico sem role PACIENTE não acessa endpoints do portal do paciente."""
    resp = api.get(
        "/cuidado/paciente/me/journeys",
        headers=clinico_headers,
    )
    assert resp.status_code == 403, (
        f"Esperado 403 para clínico em endpoint paciente, obtido {resp.status_code}"
    )
