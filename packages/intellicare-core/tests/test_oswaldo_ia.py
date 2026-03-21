"""Testes DEM-061 — Oswaldo IA: Sugestão CID-10 + Prescrição (Hybrid)."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from modules.oswaldo.api.routes import router as oswaldo_router

TENANT_SLUG = "oswaldo_test_ia"


def _mock_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug=TENANT_SLUG,
        user_id="clinico-ow-1",
        roles=["CLINICO"],
        email="clinico_ow@test.local",
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(oswaldo_router, prefix="/api/v1/oswaldo")
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
async def test_suggest_rule_based(client: AsyncClient, monkeypatch):
    """Sem LLM configurado, retorna sugestão de regras."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await client.post("/api/v1/oswaldo/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de garganta há 3 dias",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "rule-based"
    assert data["confidence"] == "low"
    assert data["cid10_code"] == "Z00"
    assert isinstance(data["prescription_items"], list)


# ────────────────────────────────────────────────────────────────────────────
# Test 2: Campo chief_complaint obrigatório
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_missing_complaint(client: AsyncClient):
    """Campo chief_complaint obrigatório — 422 sem ele."""
    resp = await client.post("/api/v1/oswaldo/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
    })
    assert resp.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# Test 3: Role check — não-CLINICO recebe 403
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_forbidden_role():
    """Usuário sem role CLINICO recebe 403."""
    def _gestor_ctx():
        return TenantContext.from_slug(
            slug=TENANT_SLUG,
            user_id="gestor-1",
            roles=["GESTOR"],
            email="gestor@test.local",
        )

    app = FastAPI()
    app.include_router(oswaldo_router, prefix="/api/v1/oswaldo")
    app.dependency_overrides[get_current_tenant] = _gestor_ctx

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/api/v1/oswaldo/suggest", json={
            "encounter_id": 1,
            "patient_id": 1,
            "chief_complaint": "Teste",
        })
        assert resp.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# Test 4: Mock LLM retorna sugestão com confidence high
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_with_llm_mock(client: AsyncClient, monkeypatch):
    """Com LLM mockado, retorna CID-10 e itens com confidence high."""
    async def mock_call_llm(prompt: str) -> dict:
        return {
            "cid10_code": "J03.9",
            "cid10_desc": "Amigdalite aguda não especificada",
            "items": [
                {"drug": "Amoxicilina 500mg", "posology": "1 cap 8/8h", "duration": "7 dias"},
            ],
            "model": "gpt-4o-mini",
        }

    monkeypatch.setattr("modules.oswaldo.services.call_llm", mock_call_llm)
    resp = await client.post("/api/v1/oswaldo/suggest", json={
        "encounter_id": 1,
        "patient_id": 1,
        "chief_complaint": "Dor de garganta",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "high"
    assert data["cid10_code"] == "J03.9"
    assert len(data["prescription_items"]) == 1
    assert data["prescription_items"][0]["drug"] == "Amoxicilina 500mg"


# ────────────────────────────────────────────────────────────────────────────
# Test 5: Rule-based retorna lista vazia de itens
# ────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_suggest_rule_based_empty_items(client: AsyncClient, monkeypatch):
    """Rule-based retorna lista vazia de prescription_items."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await client.post("/api/v1/oswaldo/suggest", json={
        "encounter_id": 3,
        "patient_id": 3,
        "chief_complaint": "Cefaleia",
        "recent_diagnoses": ["G43"],
        "current_medications": ["Sumatriptano 50mg"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["prescription_items"] == []
    assert data["confidence"] == "low"
