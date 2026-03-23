import pytest
from datetime import date, timedelta
from uuid import uuid4, UUID
from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session, get_engine
from intellicare_core.db.migrations import provision_tenant_schema
from modules.admin.kpis import get_clinical_kpis
from modules.admin.schemas import ClinicalKPIsResponse

TEST_SLUG = "admin_kpis_test"

@pytest.fixture(scope="module", autouse=True)
async def setup_kpis_schema():
    await provision_tenant_schema(TEST_SLUG)
    async with get_engine().begin() as conn:
        await conn.execute(text(f'SET search_path TO "tenant_{TEST_SLUG}"'))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS professionals (id UUID PRIMARY KEY, name TEXT, keycloak_id TEXT)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS patients (id UUID PRIMARY KEY, name TEXT)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS encounters (id UUID PRIMARY KEY, patient_id UUID, clinician_id TEXT, professional_id UUID, status TEXT, opened_at TIMESTAMPTZ)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS encounter_notes (encounter_id UUID, patient_id UUID, professional_id UUID, author_id TEXT, author_name TEXT, note_type TEXT, created_at TIMESTAMPTZ)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS prescriptions (id UUID PRIMARY KEY, encounter_id UUID, patient_id UUID, professional_id UUID, author_id TEXT, author_name TEXT, interaction_warnings_count INT, created_at TIMESTAMPTZ)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS journeys (id UUID PRIMARY KEY, patient_id UUID, status TEXT, created_at TIMESTAMPTZ)"))

@pytest.fixture
def mock_context():
    return TenantContext(
        tenant_id=f"tenant_{TEST_SLUG}",
        schema=f"tenant_{TEST_SLUG}",
        user_id="d1b11b5e-f7fa-4aee-b2ca-117565eb634e",
        email="test@kpis.com",
        roles=["GESTOR"],
    )

@pytest.fixture(autouse=True)
async def clear_db(mock_context):
    async with tenant_session(mock_context) as db:
        await db.execute(text("DELETE FROM prescriptions"))
        await db.execute(text("DELETE FROM encounter_notes"))
        await db.execute(text("DELETE FROM encounters"))
        await db.execute(text("DELETE FROM journeys"))
        await db.execute(text("DELETE FROM professionals"))

@pytest.mark.asyncio
async def test_kpis_empty_period(mock_context):
    today = date.today()
    # Empty period
    res = await get_clinical_kpis(mock_context, today, today)
    assert res.encounters == 0
    assert res.notes == 0
    assert res.prescriptions == 0
    assert res.interactions_detected == 0
    assert res.journeys == {}
    assert len(res.top_professionals) == 0
    assert len(res.interactions_by_day) == 0


@pytest.mark.asyncio
async def test_kpis_returns_correct_counts(mock_context):
    """Inserts mock data and verifies counts."""
    async with tenant_session(mock_context) as db:
        prof_id = uuid4()
        patient_id = uuid4()
        
        await db.execute(text("""
            INSERT INTO professionals (id, name, keycloak_id) 
            VALUES (:id, 'Test Prof', :kc)
        """), {"id": prof_id, "kc": str(prof_id)})

        # 2 encounters - 1 closed
        await db.execute(text("""
            INSERT INTO encounters (id, patient_id, clinician_id, status, opened_at) 
            VALUES 
            (:e1, :pat, :prof, 'closed', NOW()),
            (:e2, :pat, :prof, 'open', NOW())
        """), {"e1": uuid4(), "e2": uuid4(), "pat": str(patient_id), "prof": str(prof_id)})

        # 2 notes
        await db.execute(text("""
            INSERT INTO encounter_notes (encounter_id, patient_id, author_id, author_name, note_type, created_at)
            VALUES 
            (:e1, :pat, :prof, 'N', 'T', NOW()),
            (:e2, :pat, :prof, 'N', 'T', NOW())
        """), {"e1": uuid4(), "e2": uuid4(), "pat": str(patient_id), "prof": str(prof_id)})

        # 3 prescriptions - 2 with interactions
        await db.execute(text("""
            INSERT INTO prescriptions (id, patient_id, author_id, interaction_warnings_count, created_at)
            VALUES 
            (:p1, :pat, :prof, 4, NOW()),
            (:p2, :pat, :prof, 1, NOW()),
            (:p3, :pat, :prof, 0, NOW())
        """), {"p1": uuid4(), "p2": uuid4(), "p3": uuid4(), "pat": str(patient_id), "prof": str(prof_id)})

        # 2 journeys
        await db.execute(text("""
            INSERT INTO journeys (id, patient_id, status, created_at)
            VALUES 
            (:j1, :pat, 'active', NOW()),
            (:j2, :pat, 'completed', NOW())
        """), {"j1": uuid4(), "j2": uuid4(), "pat": str(patient_id)})

    today = date.today()
    res = await get_clinical_kpis(mock_context, today - timedelta(days=1), today + timedelta(days=1))
    
    assert res.encounters == 1
    assert res.notes == 2
    assert res.prescriptions == 3
    assert res.interactions_detected == 2
    assert res.journeys.get("active") == 1
    assert res.journeys.get("completed") == 1
    assert res.top_professionals[0]["name"] == "Test Prof"
    assert res.top_professionals[0]["total"] == 3
    assert res.interactions_by_day[0]["day"] == str(today)
    assert res.interactions_by_day[0]["total"] == 2

    # Test filtering by professional
    fake_prof = uuid4()
    res_filtered = await get_clinical_kpis(mock_context, today - timedelta(days=1), today + timedelta(days=1), professional_id=fake_prof)
    
    assert res_filtered.encounters == 0
    assert res_filtered.notes == 0
    assert res_filtered.prescriptions == 0
    assert res_filtered.interactions_detected == 2
