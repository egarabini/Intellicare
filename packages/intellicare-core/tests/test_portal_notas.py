from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts import TenantContext
from intellicare_core.db.session import get_engine
from intellicare_core.db.migrations import provision_tenant_schema
from intellicare_core.main import app
from modules.careplanner.migrations import CAREPLANNER_MIGRATIONS
from modules.gestor.migrations import GESTOR_MIGRATIONS


TEST_SLUG = "portal_notas_test"


@pytest.fixture(scope="module", autouse=True)
async def setup_portal_notas_schema():
    await provision_tenant_schema(TEST_SLUG)

    async with get_engine().begin() as conn:
        await conn.execute(text(f'SET search_path TO "tenant_{TEST_SLUG}"'))
        for sql in GESTOR_MIGRATIONS:
            await conn.execute(text(sql))
        for sql in CAREPLANNER_MIGRATIONS:
            await conn.execute(text(sql))
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS encounters (
                    id UUID PRIMARY KEY,
                    patient_id UUID NOT NULL,
                    clinician_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    cid10_code TEXT,
                    prescription TEXT,
                    chief_complaint TEXT,
                    priority TEXT,
                    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    closed_at TIMESTAMPTZ
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS clinical_notes (
                    id SERIAL PRIMARY KEY,
                    encounter_id UUID NOT NULL,
                    patient_id UUID NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    note_type TEXT NOT NULL,
                    soap_s TEXT,
                    soap_o TEXT,
                    soap_a TEXT,
                    soap_p TEXT,
                    free_text TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        await conn.execute(text("SET search_path TO public"))


def override_paciente_tenant():
    return TenantContext.from_slug(
        slug=TEST_SLUG,
        user_id="paciente-keycloak-id",
        email="paciente.portal@test.com",
        roles=["PACIENTE"],
    )


def override_gestor_tenant():
    return TenantContext.from_slug(
        slug=TEST_SLUG,
        user_id="gestor-keycloak-id",
        email="gestor.portal@test.com",
        roles=["TENANT_GESTOR"],
    )


@pytest.fixture
async def async_client_paciente():
    app.dependency_overrides[get_current_tenant] = override_paciente_tenant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client_gestor():
    app.dependency_overrides[get_current_tenant] = override_gestor_tenant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_patient_portal_data():
    patient_id = str(uuid4())
    appointment_id = str(uuid4())
    clinician_id = str(uuid4())
    encounter_id = str(uuid4())

    async with get_engine().begin() as conn:
        await conn.execute(text(f'SET search_path TO "tenant_{TEST_SLUG}"'))
        await conn.execute(text("DELETE FROM care_tasks"))
        await conn.execute(text("DELETE FROM clinical_notes"))
        await conn.execute(text("DELETE FROM encounters"))
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
        await conn.execute(
            text(
                """
                INSERT INTO encounters (id, patient_id, clinician_id, status, opened_at, closed_at)
                VALUES (:id, :patient_id, :clinician_id, 'closed', now() - interval '1 day', now() - interval '23 hour')
                """
            ),
            {
                "id": encounter_id,
                "patient_id": patient_id,
                "clinician_id": clinician_id,
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO clinical_notes (
                    encounter_id, patient_id, author_id, author_name,
                    note_type, soap_s, soap_o, soap_a, soap_p, free_text
                )
                VALUES (
                    :encounter_id, :patient_id, :author_id, :author_name,
                    'SOAP', :soap_s, :soap_o, :soap_a, :soap_p, NULL
                )
                """
            ),
            {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "author_id": clinician_id,
                "author_name": "Dra. Alice Souza",
                "soap_s": "Dor de cabeça há 2 dias",
                "soap_o": "PA 120/80, FC 72 bpm",
                "soap_a": "Cefaleia tensional provável",
                "soap_p": "Hidratação, repouso e analgesia se necessário",
            },
        )
        await conn.execute(text("SET search_path TO public"))

    return {
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "encounter_id": encounter_id,
    }


@pytest.mark.asyncio
async def test_my_journeys_empty(async_client_paciente, seed_patient_portal_data):
    resp = await async_client_paciente.get("/cuidado/paciente/me/journeys")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_my_clinical_notes_no_soap_a(async_client_paciente, seed_patient_portal_data):
    resp = await async_client_paciente.get("/cuidado/paciente/me/clinical-notes")
    assert resp.status_code == 200
    notes = resp.json()
    assert len(notes) > 0
    for note in notes:
        assert "soap_a" not in note
        assert "Avaliação" not in note.get("summary", "")
        assert "Cefaleia tensional provável" not in note.get("summary", "")


@pytest.mark.asyncio
async def test_portal_requires_paciente_role(async_client_gestor):
    resp = await async_client_gestor.get("/cuidado/paciente/me/journeys")
    assert resp.status_code == 403
