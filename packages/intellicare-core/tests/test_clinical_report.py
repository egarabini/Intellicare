import pytest
from sqlalchemy import text
from httpx import ASGITransport, AsyncClient
from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts import TenantContext
from intellicare_core.main import app

def override_clinico_tenant():
    return TenantContext.from_slug(
        slug="test_tenant",
        user_id="clinico-keycloak-id",
        email="clinico@test.com",
        roles=["CLINICO", "GESTOR"],
    )

@pytest.fixture
async def async_client():
    app.dependency_overrides[get_current_tenant] = override_clinico_tenant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
@pytest.fixture(scope="module", autouse=True)
async def setup_clinical_report_schema():
    from intellicare_core.db.migrations import provision_tenant_schema
    from intellicare_core.db.session import get_engine
    
    await provision_tenant_schema("test_tenant")
    
    async with get_engine().begin() as conn:
        await conn.execute(text('SET search_path TO "tenant_test_tenant"'))
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
                    id BIGSERIAL PRIMARY KEY,
                    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
                    patient_id UUID NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    note_type TEXT NOT NULL,
                    soap_s TEXT,
                    soap_o TEXT,
                    soap_a TEXT,
                    soap_p TEXT,
                    free_text TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS prescriptions (
                    id BIGSERIAL PRIMARY KEY,
                    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
                    patient_id UUID NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    cid10_code TEXT,                    
                    cid10_desc TEXT,                    
                    items JSONB NOT NULL DEFAULT '[]',
                    notes TEXT,
                    status TEXT NOT NULL DEFAULT 'DRAFT',  
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )

        
        await conn.execute(text("INSERT INTO encounters (id, patient_id, clinician_id) VALUES ('22222222-2222-2222-2222-222222222222', '12345678-1234-5678-1234-567812345678', 'clinico-keycloak-id') ON CONFLICT DO NOTHING"))
        
        await conn.execute(text("INSERT INTO clinical_notes (encounter_id, patient_id, author_id, author_name, note_type, free_text) VALUES ('22222222-2222-2222-2222-222222222222', '12345678-1234-5678-1234-567812345678', 'clinico-keycloak-id', 'Doutor', 'FREE', 'Paciente com queixas') ON CONFLICT DO NOTHING"))

        await conn.execute(text("SET search_path TO public"))
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tenant_users (
                    keycloak_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
                """
            )
        )
        await conn.execute(text("INSERT INTO patients (id, name) VALUES ('12345678-1234-5678-1234-567812345678', 'Paciente Teste') ON CONFLICT DO NOTHING"))
        await conn.execute(text("INSERT INTO tenant_users (keycloak_id, name) VALUES ('clinico-keycloak-id', 'Doutor Teste') ON CONFLICT DO NOTHING"))


pytestmark = pytest.mark.asyncio

async def test_clinical_report_pdf_valid(async_client):
    """PDF gerado começa com %PDF."""
    resp = await async_client.get("/cuidado/encounters/22222222-2222-2222-2222-222222222222/report.pdf")
    
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"

async def test_clinical_report_not_found(async_client):
    resp = await async_client.get("/cuidado/encounters/00000000-0000-0000-0000-000000000000/report.pdf")
    assert resp.status_code == 404
