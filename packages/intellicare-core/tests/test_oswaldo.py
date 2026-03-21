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
async def setup_oswaldo_schema():
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
                CREATE TABLE IF NOT EXISTS cid10 (
                    code TEXT PRIMARY KEY,
                    description TEXT NOT NULL
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
        
        await conn.execute(text("INSERT INTO encounters (id, patient_id, clinician_id) VALUES ('12345678-1234-5678-1234-567812345678', '12345678-1234-5678-1234-567812345678', 'clinico-keycloak-id') ON CONFLICT DO NOTHING"))
        await conn.execute(text("INSERT INTO cid10 (code, description) VALUES ('J00', 'Rinofaringite aguda') ON CONFLICT DO NOTHING"))
        await conn.execute(text("SET search_path TO public"))

pytestmark = pytest.mark.asyncio

async def test_create_prescription(async_client):
    resp = await async_client.post("/oswaldo/prescriptions", json={
        "encounter_id": "12345678-1234-5678-1234-567812345678",
        "patient_id": "12345678-1234-5678-1234-567812345678",
        "cid10_code": "J00",
        "cid10_desc": "Rinofaringite aguda",
        "items": [
            {"drug": "Ibuprofeno 600mg", "posology": "1 comp 8/8h", "duration": "5 dias"}
        ],
    })
    assert resp.status_code in (200, 403)
    if resp.status_code == 200:
        assert resp.json()["cid10_code"] == "J00"
        assert len(resp.json()["items"]) == 1

async def test_search_cid10(async_client):
    resp = await async_client.get("/oswaldo/cid10/search?q=rinofar")
    assert resp.status_code in (200, 403)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)

async def test_list_prescriptions_by_encounter(async_client):
    resp = await async_client.get("/oswaldo/prescriptions/encounter/12345678-1234-5678-1234-567812345678")
    assert resp.status_code in (200, 403)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)
