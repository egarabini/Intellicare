"""Tests for FHIRSQLBuilder — 20 scenarios."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from intellicare_core.fhir_storage.models import FHIRStorageBase
from intellicare_core.fhir_storage.repository import FHIRRepository
from intellicare_core.fhir_search.sql_builder import FHIRSQLBuilder
from intellicare_core.fhir_search.parser import parse_search_params
from intellicare_core.fhir_search.models import SearchRequest

TEST_DB = "sqlite+aiosqlite:///:memory:"
TENANT = "tenant-test"


# ── Fixtures ──────────────────────────────────────────────────────────────────


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
async def repo(session: AsyncSession) -> FHIRRepository:
    return FHIRRepository(session, tenant_id=TENANT)


@pytest_asyncio.fixture
async def builder(session: AsyncSession) -> FHIRSQLBuilder:
    return FHIRSQLBuilder(session)


async def _seed_patient(repo: FHIRRepository, overrides: dict | None = None) -> dict:
    """Create a minimal Patient resource."""
    base = {
        "resourceType": "Patient",
        "gender": "female",
        "birthDate": "1990-05-15",
        "active": True,
        "name": [{"family": "Silva", "given": ["Maria"]}],
        "identifier": [{"system": "http://cpf.gov.br", "value": "12345678901"}],
    }
    if overrides:
        base.update(overrides)
    return await repo.create(base)


# ── No-filter search ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_search_returns_all(repo, builder) -> None:
    await _seed_patient(repo)
    await _seed_patient(repo)
    req = parse_search_params("Patient", {})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 2


@pytest.mark.asyncio
async def test_empty_search_excludes_deleted(repo, builder) -> None:
    p = await _seed_patient(repo)
    await repo.delete("Patient", p["id"])
    req = parse_search_params("Patient", {})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 0


# ── _id filter ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_id_filter_returns_exact_resource(repo, builder) -> None:
    p = await _seed_patient(repo)
    req = parse_search_params("Patient", {"_id": p["id"]})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 1
    assert result.resources[0]["id"] == p["id"]


@pytest.mark.asyncio
async def test_id_filter_no_match_returns_empty(repo, builder) -> None:
    await _seed_patient(repo)
    req = parse_search_params("Patient", {"_id": "ghost-id"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 0


# ── Token filter ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_token_gender_filter(repo, builder) -> None:
    await _seed_patient(repo, {"gender": "female"})
    await _seed_patient(repo, {"gender": "male"})
    req = parse_search_params("Patient", {"gender": "female"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 1
    assert result.resources[0]["gender"] == "female"


# ── Array path filter (name) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_array_name_filter_matches(repo, builder) -> None:
    await _seed_patient(repo, {"name": [{"family": "Silva"}]})
    await _seed_patient(repo, {"name": [{"family": "Santos"}]})
    req = parse_search_params("Patient", {"name": "silva"})
    result = await builder.execute(TENANT, req)
    # LIKE on JSON text — should match "Silva"
    assert len(result.resources) >= 1
    families = [r["name"][0]["family"].lower() for r in result.resources]
    assert "silva" in families


@pytest.mark.asyncio
async def test_contains_modifier_on_name(repo, builder) -> None:
    await _seed_patient(repo, {"name": [{"family": "Goncalves"}]})
    await _seed_patient(repo, {"name": [{"family": "Pereira"}]})
    req = parse_search_params("Patient", {"name:contains": "calves"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) >= 1


# ── Date filter ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_date_filter_gt(repo, builder) -> None:
    await _seed_patient(repo, {"birthDate": "1985-01-01"})
    await _seed_patient(repo, {"birthDate": "2000-06-15"})
    req = parse_search_params("Patient", {"birthdate": "gt1990-01-01"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 1
    assert result.resources[0]["birthDate"] == "2000-06-15"


@pytest.mark.asyncio
async def test_date_filter_le(repo, builder) -> None:
    await _seed_patient(repo, {"birthDate": "1980-01-01"})
    await _seed_patient(repo, {"birthDate": "2005-03-10"})
    req = parse_search_params("Patient", {"birthdate": "le1990-12-31"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 1
    assert result.resources[0]["birthDate"] == "1980-01-01"


# ── Tenant isolation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation(session, repo, builder) -> None:
    await _seed_patient(repo)  # in TENANT
    other_repo = FHIRRepository(session, tenant_id="other-tenant")
    await _seed_patient(other_repo)
    req = parse_search_params("Patient", {})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 1


# ── Pagination ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_count_limits_results(repo, builder) -> None:
    for _ in range(5):
        await _seed_patient(repo)
    req = parse_search_params("Patient", {"_count": "3"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 3


@pytest.mark.asyncio
async def test_offset_skips_records(repo, builder) -> None:
    for _ in range(4):
        await _seed_patient(repo)
    req = parse_search_params("Patient", {"_count": "10", "_offset": "2"})
    result = await builder.execute(TENANT, req)
    assert len(result.resources) == 2


@pytest.mark.asyncio
async def test_next_offset_set_when_full_page(repo, builder) -> None:
    for _ in range(3):
        await _seed_patient(repo)
    req = parse_search_params("Patient", {"_count": "3"})
    result = await builder.execute(TENANT, req)
    assert result.next_offset == 3


@pytest.mark.asyncio
async def test_next_offset_none_on_partial_page(repo, builder) -> None:
    await _seed_patient(repo)
    req = parse_search_params("Patient", {"_count": "10"})
    result = await builder.execute(TENANT, req)
    assert result.next_offset is None


# ── Total (accurate count) ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_total_accurate_returns_count(repo, builder) -> None:
    for _ in range(3):
        await _seed_patient(repo)
    req = parse_search_params("Patient", {"_total": "accurate", "_count": "1"})
    result = await builder.execute(TENANT, req)
    assert result.total == 3


# ── Unknown param ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unknown_search_param_ignored_no_error(repo, builder) -> None:
    await _seed_patient(repo)
    req = parse_search_params("Patient", {"totally-unknown-param": "value"})
    result = await builder.execute(TENANT, req)
    # Should not raise, just return all
    assert len(result.resources) == 1


# ── Resource type isolation ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resource_type_filter(repo, builder) -> None:
    await _seed_patient(repo)
    await repo.create({
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "BP"},
        "subject": {"reference": "Patient/p-001"},
    })
    req = parse_search_params("Patient", {})
    result = await builder.execute(TENANT, req)
    assert all(r["resourceType"] == "Patient" for r in result.resources)
    assert len(result.resources) == 1
