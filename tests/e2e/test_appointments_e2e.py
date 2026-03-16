"""E2E — DEM-029: Robustez do módulo de agendamento."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e

FAKE_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(scope="module")
def paciente_headers() -> dict[str, str]:
    """Token do paciente.alfa (tenant_alfa)."""
    from .conftest import get_token, auth_headers
    return auth_headers(get_token("paciente.alfa", "Demo@1234"))


def test_confirm_nonexistent_appointment_returns_404(
    api: httpx.Client, paciente_headers: dict
):
    """PATCH confirm em appointment inexistente deve retornar 404."""
    resp = api.patch(
        f"/cuidado/appointments/{FAKE_UUID}/confirm",
        headers=paciente_headers,
    )
    assert resp.status_code == 404


def test_cancel_nonexistent_appointment_returns_404(
    api: httpx.Client, paciente_headers: dict
):
    """PATCH cancel em appointment inexistente deve retornar 404."""
    resp = api.patch(
        f"/cuidado/appointments/{FAKE_UUID}/cancel",
        headers=paciente_headers,
    )
    assert resp.status_code == 404
