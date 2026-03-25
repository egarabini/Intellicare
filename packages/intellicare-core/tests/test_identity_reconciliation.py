from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_platform_db
from modules.identity.router import router as identity_router
from modules.identity.schemas import IdentityReconcileResult, PessoaFisicaIn
from modules.identity import services as identity_services


ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="admin-uid",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)

GESTOR_CTX = TenantContext(
    tenant_id="alfa",
    schema="tenant_alfa",
    user_id="gestor-uid",
    roles=["TENANT_GESTOR"],
    email="gestor@test.dev",
)


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._scalar


class FakeTenantSession:
    def __init__(self, select_rows: list[dict] | None = None):
        self.select_rows = select_rows or []
        self.updated: list[dict] = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        if sql.strip().upper().startswith("SELECT"):
            return FakeResult(rows=self.select_rows)
        self.updated.append(params or {})
        return FakeResult()


def _build_client(ctx: TenantContext) -> TestClient:
    app = FastAPI()
    app.include_router(identity_router)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    async def _fake_platform_db():
        yield object()
    app.dependency_overrides[get_platform_db] = _fake_platform_db
    return TestClient(app)


@pytest.mark.asyncio
async def test_reconcile_patients_links_existing_cpf(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeTenantSession(
        select_rows=[{"id": "p1", "nome_completo": "Maria Legacy", "cpf": "123.456.789-01"}]
    )
    linked: list[tuple[str, str]] = []

    @asynccontextmanager
    async def fake_tenant_session(ctx):
        assert ctx.tenant_id == "alfa"
        yield session

    async def fake_find_or_create(payload: PessoaFisicaIn):
        assert payload.nome_completo == "Maria Legacy"
        assert payload.cpf == "123.456.789-01"
        return {"id": uuid4()}

    async def fake_register(platform_db, pessoa_id, tenant_slug):
        linked.append((str(pessoa_id), tenant_slug))

    monkeypatch.setattr(identity_services, "tenant_session", fake_tenant_session)
    monkeypatch.setattr(identity_services, "find_or_create_by_cpf", fake_find_or_create)
    monkeypatch.setattr(identity_services, "register_tenant_link", fake_register)
    monkeypatch.setattr(identity_services, "table_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "column_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "_patient_name_column", lambda *args: _async_return("name"))

    ctx = TenantContext.from_slug("alfa", "admin", ["PLATFORM_ADMIN"])
    result = await identity_services.reconcile_tenant_patients(ctx, platform_db=object())

    assert result.processed == 1
    assert result.linked == 1
    assert result.skipped == 0
    assert result.errors == []
    assert session.updated[0]["id"] == "p1"
    assert linked[0][1] == "alfa"


@pytest.mark.asyncio
async def test_reconcile_is_idempotent_on_second_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions = [
        FakeTenantSession(select_rows=[{"id": "p1", "nome_completo": "Maria Legacy", "cpf": "12345678901"}]),
        FakeTenantSession(select_rows=[]),
    ]

    @asynccontextmanager
    async def fake_tenant_session(ctx):
        yield sessions.pop(0)

    monkeypatch.setattr(identity_services, "tenant_session", fake_tenant_session)
    monkeypatch.setattr(identity_services, "find_or_create_by_cpf", lambda payload: _async_return({"id": uuid4()}))
    monkeypatch.setattr(identity_services, "register_tenant_link", lambda *args: _async_return(None))
    monkeypatch.setattr(identity_services, "table_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "column_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "_patient_name_column", lambda *args: _async_return("name"))

    ctx = TenantContext.from_slug("alfa", "admin", ["PLATFORM_ADMIN"])
    first = await identity_services.reconcile_tenant_patients(ctx, platform_db=object())
    second = await identity_services.reconcile_tenant_patients(ctx, platform_db=object())

    assert first.linked == 1
    assert second.linked == 0
    assert second.processed == 0


@pytest.mark.asyncio
async def test_reconcile_skip_blank_cpf(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeTenantSession(select_rows=[{"id": "p1", "nome_completo": "Sem CPF", "cpf": ""}])

    @asynccontextmanager
    async def fake_tenant_session(ctx):
        yield session

    monkeypatch.setattr(identity_services, "tenant_session", fake_tenant_session)
    monkeypatch.setattr(identity_services, "find_or_create_by_cpf", lambda payload: _async_return({"id": uuid4()}))
    monkeypatch.setattr(identity_services, "register_tenant_link", lambda *args: _async_return(None))
    monkeypatch.setattr(identity_services, "table_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "column_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "_patient_name_column", lambda *args: _async_return("name"))

    ctx = TenantContext.from_slug("alfa", "admin", ["PLATFORM_ADMIN"])
    result = await identity_services.reconcile_tenant_patients(ctx, platform_db=object())

    assert result.processed == 1
    assert result.linked == 0
    assert result.skipped == 1
    assert result.errors == []


@pytest.mark.asyncio
async def test_reconcile_error_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeTenantSession(
        select_rows=[
            {"id": "p1", "nome_completo": "Erro", "cpf": "12345678901"},
            {"id": "p2", "nome_completo": "OK", "cpf": "98765432100"},
        ]
    )

    @asynccontextmanager
    async def fake_tenant_session(ctx):
        yield session

    async def fake_find_or_create(payload: PessoaFisicaIn):
        if payload.nome_completo == "Erro":
            raise RuntimeError("cpf duplicado corrompido")
        return {"id": uuid4()}

    monkeypatch.setattr(identity_services, "tenant_session", fake_tenant_session)
    monkeypatch.setattr(identity_services, "find_or_create_by_cpf", fake_find_or_create)
    monkeypatch.setattr(identity_services, "register_tenant_link", lambda *args: _async_return(None))
    monkeypatch.setattr(identity_services, "table_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "column_exists", lambda *args: _async_return(True))
    monkeypatch.setattr(identity_services, "_patient_name_column", lambda *args: _async_return("name"))

    ctx = TenantContext.from_slug("alfa", "admin", ["PLATFORM_ADMIN"])
    result = await identity_services.reconcile_tenant_patients(ctx, platform_db=object())

    assert result.processed == 2
    assert result.linked == 1
    assert result.skipped == 0
    assert len(result.errors) == 1
    assert result.errors[0].record_id == "p1"


@pytest.mark.asyncio
async def test_identity_stats_returns_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_table_exists(schema: str, table_name: str) -> bool:
        return True

    async def fake_column_exists(schema: str, table_name: str, column_name: str) -> bool:
        return column_name == "pessoa_id"

    async def fake_count(ctx: TenantContext, table_name: str) -> int:
        return 10 if table_name == "patients" else 4

    async def fake_linked(ctx: TenantContext, table_name: str) -> int:
        return 7 if table_name == "patients" else 2

    monkeypatch.setattr(identity_services, "list_tenants", lambda: _async_return([
        {"slug": "alfa", "status": "active"},
        {"slug": "beta", "status": "suspended"},
    ]))
    monkeypatch.setattr(identity_services, "count_pessoas_fisicas", lambda: _async_return(20))
    monkeypatch.setattr(identity_services, "table_exists", fake_table_exists)
    monkeypatch.setattr(identity_services, "column_exists", fake_column_exists)
    monkeypatch.setattr(identity_services, "_tenant_table_count", fake_count)
    monkeypatch.setattr(identity_services, "_tenant_linked_count", fake_linked)

    stats = await identity_services.get_identity_stats()

    assert stats.total_pessoas == 20
    assert stats.patients_total == 20
    assert stats.patients_linked == 14
    assert stats.professionals_total == 8
    assert stats.professionals_linked == 4
    assert stats.coverage_pct == 64.29
    assert stats.tenants[0].coverage_pct == 64.29


def test_reconcile_requires_platform_admin() -> None:
    client = _build_client(GESTOR_CTX)
    response = client.post("/identity/admin/reconcile?scope=patients")

    assert response.status_code == 403


async def _async_return(value):
    return value
