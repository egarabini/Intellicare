from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from modules.identity.router import router as identity_router
from modules.identity.schemas import PessoaFisicaIn
from modules.identity.services import find_or_create_by_cpf, normalize_cpf


ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="admin-uid",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)


def _build_app() -> TestClient:
    app = FastAPI()
    app.include_router(identity_router)
    app.dependency_overrides[get_current_tenant] = lambda: ADMIN_CTX
    return TestClient(app)


def test_normalize_cpf_strips_formatting() -> None:
    assert normalize_cpf("123.456.789-01") == "12345678901"


def test_normalize_cpf_invalid_length() -> None:
    with pytest.raises(ValueError, match="CPF invalido"):
        normalize_cpf("123")


@pytest.mark.asyncio
async def test_find_or_create_by_cpf_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    pessoa_id = uuid4()
    payload = PessoaFisicaIn(nome_completo="Maria Teste", cpf="123.456.789-01")
    existing = {
        "id": pessoa_id,
        "tipo": "FISICA",
        "nome_completo": "Maria Teste",
        "cpf": "12345678901",
        "data_nascimento": None,
        "genero": None,
    }

    first_call = {"done": False}

    async def fake_get(cpf: str):
        assert cpf == "12345678901"
        if first_call["done"]:
            return existing
        first_call["done"] = True
        return None

    async def fake_create(payload_in: PessoaFisicaIn, cpf_clean: str):
        assert payload_in.nome_completo == "Maria Teste"
        assert cpf_clean == "12345678901"
        return existing

    monkeypatch.setattr("modules.identity.services.get_pessoa_by_cpf", fake_get)
    monkeypatch.setattr("modules.identity.services.create_pessoa_fisica", fake_create)

    created = await find_or_create_by_cpf(payload)
    fetched = await find_or_create_by_cpf(payload)

    assert created["id"] == fetched["id"] == pessoa_id


def test_lookup_by_cpf_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    pessoa_id = uuid4()

    async def fake_lookup(cpf: str):
        assert cpf == "12345678901"
        return {
            "id": pessoa_id,
            "tipo": "FISICA",
            "nome_completo": "Joao da Silva",
            "cpf": "12345678901",
            "data_nascimento": "1990-01-01",
            "genero": "MASCULINO",
        }

    monkeypatch.setattr("modules.identity.router.get_pessoa_by_cpf", fake_lookup)
    client = _build_app()
    response = client.get("/identity/pessoas/cpf/123.456.789-01")

    assert response.status_code == 200
    assert response.json()["nome_completo"] == "Joao da Silva"


def test_lookup_by_cpf_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_lookup(cpf: str):
        assert cpf == "00000000000"
        return None

    monkeypatch.setattr("modules.identity.router.get_pessoa_by_cpf", fake_lookup)
    client = _build_app()
    response = client.get("/identity/pessoas/cpf/000.000.000-00")

    assert response.status_code == 404


def test_get_pessoa_by_id_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    pessoa_id = uuid4()

    async def fake_get(pessoa_id_in):
        assert str(pessoa_id_in) == str(pessoa_id)
        return {
            "id": pessoa_id,
            "tipo": "FISICA",
            "nome_completo": "Ana Pereira",
            "cpf": "98765432100",
            "data_nascimento": None,
            "genero": "FEMININO",
        }

    monkeypatch.setattr("modules.identity.router.get_pessoa_by_id", fake_get)
    client = _build_app()
    response = client.get(f"/identity/pessoas/{pessoa_id}")

    assert response.status_code == 200
    assert response.json()["cpf"] == "98765432100"


def test_post_identity_pessoas_returns_same_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    pessoa_id = uuid4()

    async def fake_find_or_create(payload: PessoaFisicaIn):
        assert payload.cpf == "12345678901"
        return {
            "id": pessoa_id,
            "tipo": "FISICA",
            "nome_completo": payload.nome_completo,
            "cpf": "12345678901",
            "data_nascimento": None,
            "genero": None,
        }

    monkeypatch.setattr("modules.identity.router.find_or_create_by_cpf", fake_find_or_create)
    client = _build_app()
    payload = {"nome_completo": "Maria Teste", "cpf": "12345678901"}

    first = client.post("/identity/pessoas", json=payload)
    second = client.post("/identity/pessoas", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"] == str(pessoa_id)


@pytest.mark.asyncio
async def test_migration_021_is_idempotent() -> None:
    migration_path = Path(__file__).resolve().parents[3] / "db" / "platform_migrations" / "021_pessoa_identity.sql"
    sql = migration_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]

    create_statements = [stmt for stmt in statements if stmt.upper().startswith("CREATE ")]
    assert create_statements
    assert all("IF NOT EXISTS" in stmt.upper() for stmt in create_statements)

    executed: list[str] = []

    class FakeConn:
        async def execute(self, statement):
            executed.append(str(statement))

    conn = FakeConn()
    for _ in range(2):
        for stmt in statements:
            await conn.execute(stmt)

    assert len(executed) == len(statements) * 2
