import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from uuid import uuid4

from intellicare_core.main import app
from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts import TenantContext
from intellicare_core.db.session import tenant_session
from sqlalchemy import text
from modules.gestor.migrations import GESTOR_MIGRATIONS

# Set up the event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Provide a real database schema for gestor tests
@pytest.fixture(scope="module", autouse=True)
async def setup_test_schema():
    from intellicare_core.db.migrations import provision_tenant_schema
    await provision_tenant_schema("gestor_test")
    await provision_tenant_schema("gestor_test_b")

    # Run gestor migrations manually on test schemas
    from intellicare_core.db.session import get_engine
    async with get_engine().begin() as conn:
        for schema in ["tenant_gestor_test", "tenant_gestor_test_b"]:
            await conn.execute(text(f'SET search_path TO "{schema}"'))
            # Create mock invoices table for tests
            await conn.execute(text("CREATE TABLE IF NOT EXISTS invoices (id UUID PRIMARY KEY, amount NUMERIC, status TEXT, created_at TIMESTAMPTZ, paid_at TIMESTAMPTZ)"))
            for sql in GESTOR_MIGRATIONS:
                await conn.execute(text(sql))
            
        await conn.execute(text('SET search_path TO public'))

# Mock context for Tenant A
def override_get_current_tenant_a():
    return TenantContext.from_slug(
        slug="gestor_test",
        user_id="user-gestor-123",
        email="gestor@test.com",
        roles=["TENANT_GESTOR"]
    )

# Mock context for Tenant B
def override_get_current_tenant_b():
    return TenantContext.from_slug(
        slug="gestor_test_b",
        user_id="user-gestor-456",
        email="gestor_b@test.com",
        roles=["TENANT_GESTOR"]
    )

@pytest.fixture
async def client_a():
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant_a
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def client_b():
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant_b
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

# Seeded data
@pytest.fixture
async def seed_patient(client_a):
    payload = {"name": "Test Patient", "cpf": "11122233344", "birth_date": "1990-01-01"}
    r = await client_a.post("/gestor/patients", json=payload)
    return r.json()["id"]

@pytest.fixture
def seed_clinician():
    return str(uuid4())

#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_stats(client_a):
    r = await client_a.get("/gestor/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert "patients_active" in data
    assert "appointments_today" in data

@pytest.mark.asyncio
async def test_create_patient_cpf_duplicate(client_a):
    payload = {"name": "Ana", "cpf": "12345678901", "birth_date": "1990-01-01"}
    # First creation should succeed
    r1 = await client_a.post("/gestor/patients", json=payload)
    assert r1.status_code in (200, 201)
    
    # Second should fail with 409 Conflict
    r2 = await client_a.post("/gestor/patients", json=payload)
    assert r2.status_code == 409

@pytest.mark.asyncio
async def test_appointment_conflict(client_a, seed_patient, seed_clinician):
    slot = {
        "patient_id": seed_patient, 
        "clinician_id": seed_clinician,
        "scheduled_at": "2026-04-01T09:00:00Z", 
        "type": "consulta"
    }
    r1 = await client_a.post("/gestor/appointments", json=slot)
    assert r1.status_code in (200, 201)
    
    r2 = await client_a.post("/gestor/appointments", json=slot)
    assert r2.status_code == 409

@pytest.mark.asyncio
async def test_tenant_isolation(client_b):
    r = await client_b.get("/gestor/patients")
    # should return empty list for tenant B, not patients of tenant A
    assert r.status_code == 200
    assert r.json() == []
