"""Tests for FHIRRepository — 25 scenarios."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from intellicare_core.fhir_storage.models import FHIRStorageBase, FHIRNativeResource, FHIRResourceHistory
from intellicare_core.fhir_storage.repository import FHIRRepository, ResourceNotFoundError

TEST_DB = "sqlite+aiosqlite:///:memory:"

PATIENT = {
    "resourceType": "Patient",
    "id": "p-001",
    "name": [{"family": "Silva", "given": ["Ana"]}],
    "active": True,
    "birthDate": "1985-03-15",
}

OBSERVATION = {
    "resourceType": "Observation",
    "id": "obs-001",
    "status": "final",
    "subject": {"reference": "Patient/p-001"},
    "code": {"coding": [{"code": "8867-4", "display": "Heart rate"}]},
    "valueQuantity": {"value": 72, "unit": "bpm"},
}


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DB, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(FHIRStorageBase.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(FHIRStorageBase.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
def repo(session: AsyncSession) -> FHIRRepository:
    return FHIRRepository(session, tenant_id="tenant-a")


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_assigns_id_if_missing(repo: FHIRRepository) -> None:
    resource = {"resourceType": "Patient", "active": True}
    result = await repo.create(resource)
    assert result["id"]


@pytest.mark.asyncio
async def test_create_preserves_given_id(repo: FHIRRepository) -> None:
    result = await repo.create(PATIENT)
    assert result["id"] == "p-001"


@pytest.mark.asyncio
async def test_create_injects_meta(repo: FHIRRepository) -> None:
    result = await repo.create(PATIENT)
    assert "meta" in result
    assert result["meta"]["versionId"]
    assert result["meta"]["lastUpdated"]


@pytest.mark.asyncio
async def test_create_missing_resource_type_raises(repo: FHIRRepository) -> None:
    with pytest.raises(ValueError, match="resourceType"):
        await repo.create({"id": "x"})


# ── Read ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_existing(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    result = await repo.read("Patient", "p-001")
    assert result["id"] == "p-001"
    assert result["resourceType"] == "Patient"


@pytest.mark.asyncio
async def test_read_not_found_raises(repo: FHIRRepository) -> None:
    with pytest.raises(ResourceNotFoundError):
        await repo.read("Patient", "ghost")


@pytest.mark.asyncio
async def test_read_tenant_isolation(session: AsyncSession) -> None:
    repo_a = FHIRRepository(session, "tenant-a")
    repo_b = FHIRRepository(session, "tenant-b")
    await repo_a.create(PATIENT)
    with pytest.raises(ResourceNotFoundError):
        await repo_b.read("Patient", "p-001")


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_changes_resource(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    updated = dict(PATIENT)
    updated["active"] = False
    result = await repo.update("Patient", "p-001", updated)
    assert result["active"] is False


@pytest.mark.asyncio
async def test_update_creates_new_version(repo: FHIRRepository) -> None:
    created = await repo.create(PATIENT)
    v1 = created["meta"]["versionId"]
    updated = await repo.update("Patient", "p-001", PATIENT)
    v2 = updated["meta"]["versionId"]
    assert v1 != v2


@pytest.mark.asyncio
async def test_update_not_found_raises(repo: FHIRRepository) -> None:
    with pytest.raises(ResourceNotFoundError):
        await repo.update("Patient", "ghost", PATIENT)


# ── Delete ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_soft_deletes(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.delete("Patient", "p-001")
    with pytest.raises(ResourceNotFoundError):
        await repo.read("Patient", "p-001")


@pytest.mark.asyncio
async def test_delete_idempotent(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.delete("Patient", "p-001")
    # Second delete should not raise
    await repo.delete("Patient", "p-001")


@pytest.mark.asyncio
async def test_delete_not_found_raises(repo: FHIRRepository) -> None:
    with pytest.raises(ResourceNotFoundError):
        await repo.delete("Patient", "ghost")


# ── History ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_history_returns_entries(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.update("Patient", "p-001", PATIENT)
    history = await repo.history("Patient", "p-001")
    assert len(history) == 2


@pytest.mark.asyncio
async def test_history_newest_first(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.update("Patient", "p-001", PATIENT)
    history = await repo.history("Patient", "p-001")
    first = history[0]["request"]["method"]
    assert first == "UPDATE"


@pytest.mark.asyncio
async def test_history_includes_delete(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.delete("Patient", "p-001")
    history = await repo.history("Patient", "p-001")
    methods = {e["request"]["method"] for e in history}
    assert "DELETE" in methods


@pytest.mark.asyncio
async def test_history_empty_for_nonexistent(repo: FHIRRepository) -> None:
    history = await repo.history("Patient", "ghost")
    assert history == []


@pytest.mark.asyncio
async def test_history_entry_has_full_url(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    history = await repo.history("Patient", "p-001")
    assert "fullUrl" in history[0]
    assert "_history" in history[0]["fullUrl"]


# ── Vread ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vread_specific_version(repo: FHIRRepository) -> None:
    created = await repo.create(PATIENT)
    v1_id = created["meta"]["versionId"]
    # Update — new version
    updated = dict(PATIENT)
    updated["active"] = False
    await repo.update("Patient", "p-001", updated)

    # vread v1 should return original
    v1_resource = await repo.vread("Patient", "p-001", v1_id)
    assert v1_resource["active"] is True


@pytest.mark.asyncio
async def test_vread_not_found_raises(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    with pytest.raises(ResourceNotFoundError):
        await repo.vread("Patient", "p-001", "non-existent-version-id")


# ── Search ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_returns_resources(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    results = await repo.search("Patient")
    assert len(results) == 1
    assert results[0]["id"] == "p-001"


@pytest.mark.asyncio
async def test_search_excludes_deleted(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    await repo.delete("Patient", "p-001")
    results = await repo.search("Patient")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_compartment_filter(repo: FHIRRepository) -> None:
    await repo.create(OBSERVATION)
    # Filter by Patient compartment
    results = await repo.search("Observation", compartment="Patient/p-001")
    assert len(results) == 1
    no_match = await repo.search("Observation", compartment="Patient/other")
    assert len(no_match) == 0


# ── Upsert ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_creates_when_not_exists(repo: FHIRRepository) -> None:
    result = await repo.upsert(PATIENT)
    assert result["id"] == "p-001"


@pytest.mark.asyncio
async def test_upsert_updates_when_exists(repo: FHIRRepository) -> None:
    await repo.create(PATIENT)
    updated = dict(PATIENT)
    updated["active"] = False
    result = await repo.upsert(updated)
    assert result["active"] is False
