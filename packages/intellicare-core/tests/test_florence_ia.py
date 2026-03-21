"""Testes DEM-057 — Florence IA: Sugestão SOAP (Hybrid)."""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from modules.florence.api.routes import router as florence_router

TENANT_SLUG = "florence_test_ia"


def _mock_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug=TENANT_SLUG,
        user_id="clinico-ia-1",
        roles=["CLINICO"],
        email="clinico@test.local",
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(florence_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = _mock_ctx
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ────────────────────────────────────────────────────────────────────────────
# Test 1: Sem LLM configurado, retorna sugestão rule-based
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_soap_rule_based(client: AsyncClient, monkeypatch):
    """Sem LLM configurado, retorna sugestão de regras sem erro."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await client.post("/api/v1/florence/notes/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de cabeça há 2 dias",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["soap_s"] == "Dor de cabeça há 2 dias"
    assert data["model"] == "rule-based"
    assert data["confidence"] == "low"


# ────────────────────────────────────────────────────────────────────────────
# Test 2: Campo chief_complaint obrigatório
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_soap_missing_complaint(client: AsyncClient):
    """Campo chief_complaint obrigatório — 422 sem ele."""
    resp = await client.post("/api/v1/florence/notes/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
    })
    assert resp.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# Test 3: Rule-based preenche os 4 campos corretamente
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_soap_rule_based_fields(client: AsyncClient, monkeypatch):
    """Rule-based preenche O, A, P com placeholders."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await client.post("/api/v1/florence/notes/suggest", json={
        "encounter_id": 2,
        "patient_id": 2,
        "chief_complaint": "Febre há 3 dias",
        "appointment_reason": "Consulta de retorno",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["soap_s"] == "Febre há 3 dias"
    assert "preenchido pelo clínico" in data["soap_o"].lower() or "clínico" in data["soap_o"]
    assert data["soap_a"] != ""
    assert data["soap_p"] != ""


# ────────────────────────────────────────────────────────────────────────────
# Test 4: Role check — não-CLINICO recebe 403
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_soap_forbidden_role():
    """Usuário sem role CLINICO recebe 403."""
    def _gestor_ctx():
        return TenantContext.from_slug(
            slug=TENANT_SLUG,
            user_id="gestor-1",
            roles=["GESTOR"],
            email="gestor@test.local",
        )

    app = FastAPI()
    app.include_router(florence_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = _gestor_ctx

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/api/v1/florence/notes/suggest", json={
            "encounter_id": 1,
            "patient_id": 1,
            "chief_complaint": "Teste",
        })
        assert resp.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# Test 5: Mock LLM retorna sugestão com confidence high
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_soap_with_llm_mock(client: AsyncClient, monkeypatch):
    """Com LLM mockado, retorna sugestão com confidence high."""
    async def mock_call_llm(prompt: str) -> dict:
        return {
            "S": "Paciente queixa-se de cefaleia frontal.",
            "O": "PA 130/85, FC 78bpm.",
            "A": "Cefaleia tensional.",
            "P": "Dipirona 1g VO 6/6h por 3 dias.",
            "model": "gpt-4o-mini",
        }

    monkeypatch.setattr("modules.florence.services._call_llm", mock_call_llm)
    resp = await client.post("/api/v1/florence/notes/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de cabeça",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "high"
    assert data["model"] == "gpt-4o-mini"
    assert "cefaleia" in data["soap_s"].lower()
