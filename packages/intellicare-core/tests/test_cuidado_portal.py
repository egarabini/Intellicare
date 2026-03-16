from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts import TenantContext
from intellicare_core.db.session import get_engine
from intellicare_core.main import app
from modules.gestor.migrations import GESTOR_MIGRATIONS


@pytest.fixture(scope="module", autouse=True)
async def setup_cuidado_portal_schema():
    from intellicare_core.db.migrations import provision_tenant_schema

    await provision_tenant_schema("cuidado_portal_test")

    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_cuidado_portal_test"'))
        for sql in GESTOR_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(text('SET search_path TO public'))


def override_get_current_tenant():
    return TenantContext.from_slug(
        slug="cuidado_portal_test",
        user_id="paciente-keycloak-id",
        email="paciente.portal@test.com",
        roles=["PACIENTE"],
    )


@pytest.fixture
async def paciente_client():
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_patient_data():
    patient_id = str(uuid4())
    appointment_id = str(uuid4())
    clinician_id = str(uuid4())

    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_cuidado_portal_test"'))
        await conn.execute(text("DELETE FROM appointments"))
        await conn.execute(text("DELETE FROM tenant_users"))
        await conn.execute(text("DELETE FROM patients"))

        await conn.execute(
            text(
                """
                INSERT INTO patients (id, name, cpf, birth_date, email, phone, health_plan, active)
                VALUES (:id, :name, :cpf, :birth_date, :email, :phone, :health_plan, true)
                """
            ),
            {
                "id": patient_id,
                "name": "Paciente Portal",
                "cpf": "99988877766",
                "birth_date": date(1988, 1, 2),
                "email": "paciente.portal@test.com",
                "phone": "11999999999",
                "health_plan": "DemoCare",
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO tenant_users (email, name, role, keycloak_id, status)
                VALUES (:email, :name, 'clinico', :keycloak_id, 'active')
                """
            ),
            {
                "email": "clinico.portal@test.com",
                "name": "Dra. Alice Souza",
                "keycloak_id": clinician_id,
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO appointments (id, patient_id, clinician_id, scheduled_at, type, status, notes)
                VALUES (:id, :patient_id, CAST(:clinician_id AS UUID), now() + interval '2 day', 'consulta', 'agendado', 'Trazer exames')
                """
            ),
            {
                "id": appointment_id,
                "patient_id": patient_id,
                "clinician_id": clinician_id,
            },
        )
        await conn.execute(text('SET search_path TO public'))

    return {
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "clinician_id": clinician_id,
    }


@pytest.mark.asyncio
async def test_paciente_portal_uses_email_fallback_and_clinician_name(paciente_client, seeded_patient_data):
    painel = await paciente_client.get("/cuidado/paciente/painel")
    assert painel.status_code == 200
    painel_data = painel.json()
    assert painel_data["patient_name"] == "Paciente Portal"
    assert painel_data["next_appointment"]["clinician_name"] == "Dra. Alice Souza"
    assert painel_data["upcoming_count"] == 1

    appointments = await paciente_client.get("/cuidado/paciente/appointments", params={"status": "upcoming"})
    assert appointments.status_code == 200
    items = appointments.json()
    assert len(items) == 1
    assert items[0]["clinician_name"] == "Dra. Alice Souza"
    assert items[0]["status"] == "agendado"


@pytest.mark.asyncio
async def test_paciente_can_confirm_and_cancel_appointment(paciente_client, seeded_patient_data):
    appointment_id = seeded_patient_data["appointment_id"]

    confirm = await paciente_client.patch(f"/cuidado/paciente/appointments/{appointment_id}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmado"

    cancel = await paciente_client.delete(f"/cuidado/paciente/appointments/{appointment_id}")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelado"


@pytest.mark.asyncio
async def test_paciente_confirm_missing_appointment_returns_404(paciente_client):
    missing_id = uuid4()
    response = await paciente_client.patch(f"/cuidado/paciente/appointments/{missing_id}/confirm")
    assert response.status_code == 404
