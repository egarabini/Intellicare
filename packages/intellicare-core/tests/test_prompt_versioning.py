from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intellicare_core.contracts.base import TenantContext
from modules.admin.schemas import PromptTemplateActivateRequest, PromptTemplateCreate
from modules.admin.service import TenantService
from modules.florence.contracts import SuggestRequest
from modules.florence.services import suggest_soap
from modules.oswaldo.contracts import OswaldoSuggestRequest
from modules.oswaldo.services import suggest as suggest_oswaldo
from modules.shared.llm import clear_prompt_cache, get_prompt_template

ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="admin-uid",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)


def _async_conn(execute_side_effect):
    conn = AsyncMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    conn.execute = AsyncMock(side_effect=execute_side_effect)
    return conn


@pytest.mark.asyncio
@patch("modules.shared.llm.get_engine")
async def test_get_prompt_template_uses_cache(mock_get_engine):
    clear_prompt_cache()
    result = MagicMock()
    result.scalar_one_or_none.return_value = "prompt do banco"
    conn = _async_conn([result])
    mock_engine = MagicMock()
    mock_engine.connect.return_value = conn
    mock_get_engine.return_value = mock_engine

    first = await get_prompt_template("florence_soap", "fallback")
    second = await get_prompt_template("florence_soap", "fallback")

    assert first == "prompt do banco"
    assert second == "prompt do banco"
    assert conn.execute.await_count == 1


@pytest.mark.asyncio
@patch("modules.shared.llm.get_engine", side_effect=RuntimeError("db offline"))
async def test_get_prompt_template_falls_back(mock_get_engine):
    clear_prompt_cache()
    prompt = await get_prompt_template("florence_soap", "fallback local")
    assert prompt == "fallback local"
    assert mock_get_engine.called


@pytest.mark.asyncio
async def test_florence_uses_prompt_templates(monkeypatch):
    async def fake_get_prompt_template(prompt_key: str, fallback_prompt: str) -> str:
        if prompt_key == "florence_soap":
            return "INSTRUCAO SOAP"
        return "DETALHES: {chief_complaint} / {appointment_reason} / {recent_notes}"

    captured = {}

    async def fake_call_llm(prompt: str) -> dict:
        captured["prompt"] = prompt
        return {"S": "S", "O": "O", "A": "A", "P": "P", "model": "llm-test"}

    monkeypatch.setattr("modules.florence.services.get_prompt_template", fake_get_prompt_template)
    monkeypatch.setattr("modules.florence.services.call_llm", fake_call_llm)

    result = await suggest_soap(
        ADMIN_CTX,
        SuggestRequest(
            encounter_id="enc-1",
            patient_id="pat-1",
            chief_complaint="cefaleia",
            appointment_reason="retorno",
            recent_notes=["nota 1"],
        ),
    )

    assert "INSTRUCAO SOAP" in captured["prompt"]
    assert "cefaleia / retorno / nota 1" in captured["prompt"]
    assert result.model == "llm-test"
    assert result.soap_a == "A"


@pytest.mark.asyncio
async def test_oswaldo_uses_two_prompt_templates(monkeypatch):
    async def fake_get_prompt_template(prompt_key: str, fallback_prompt: str) -> str:
        if prompt_key == "oswaldo_cid10":
            return "CID10 PRIMEIRO"
        return "PRESCRICAO DEPOIS {chief_complaint} {recent_diagnoses} {current_medications}"

    captured = {}

    async def fake_call_llm(prompt: str) -> dict:
        captured["prompt"] = prompt
        return {"cid10_code": "R51", "cid10_desc": "Cefaleia", "items": [], "model": "llm-test"}

    monkeypatch.setattr("modules.oswaldo.services.get_prompt_template", fake_get_prompt_template)
    monkeypatch.setattr("modules.oswaldo.services.call_llm", fake_call_llm)

    result = await suggest_oswaldo(
        ADMIN_CTX,
        OswaldoSuggestRequest(
            encounter_id=1,
            patient_id=1,
            chief_complaint="cefaleia",
            recent_diagnoses=["enxaqueca"],
            current_medications=["dipirona"],
        ),
    )

    assert "CID10 PRIMEIRO" in captured["prompt"]
    assert "PRESCRICAO DEPOIS cefaleia enxaqueca dipirona" in captured["prompt"]
    assert result.cid10_code == "R51"


@pytest.mark.asyncio
@patch("modules.admin.service.get_engine")
@patch("modules.admin.service.KeycloakAdminClient")
async def test_create_prompt_template_increments_version(mock_kc_cls, mock_get_engine):
    del mock_kc_cls
    next_version = MagicMock()
    next_version.scalar_one.return_value = 3
    inserted = MagicMock()
    inserted.mappings.return_value.first.return_value = {
        "id": "p1",
        "prompt_key": "florence_soap",
        "version": 3,
        "content": "novo",
        "notes": "ajuste",
        "is_active": False,
        "created_at": "2026-03-22T10:00:00Z",
        "created_by": "admin-uid",
        "created_by_email": "admin@test.dev",
        "activated_at": None,
        "activated_by": None,
        "activated_by_email": None,
    }
    conn = _async_conn([next_version, inserted, MagicMock()])
    engine = MagicMock()
    engine.begin.return_value = conn
    mock_get_engine.return_value = engine

    service = TenantService()
    result = await service.create_prompt_template(
        PromptTemplateCreate(prompt_key="florence_soap", content="novo prompt v3", notes="ajuste"),
        ADMIN_CTX,
    )

    assert result["version"] == 3
    assert result["prompt_key"] == "florence_soap"


@pytest.mark.asyncio
@patch("modules.admin.service.clear_prompt_cache")
@patch("modules.admin.service.get_engine")
@patch("modules.admin.service.KeycloakAdminClient")
async def test_activate_prompt_template_invalidates_cache(mock_kc_cls, mock_get_engine, mock_clear_prompt_cache):
    del mock_kc_cls
    found = MagicMock()
    found.mappings.return_value.first.return_value = {"id": "p2"}
    conn = _async_conn([found, MagicMock(), MagicMock(), MagicMock()])
    engine = MagicMock()
    engine.begin.return_value = conn
    mock_get_engine.return_value = engine

    service = TenantService()
    service.get_prompt_group = AsyncMock(return_value={
        "prompt_key": "florence_soap",
        "active_version": 2,
        "versions": [],
    })

    result = await service.activate_prompt_template(
        "florence_soap",
        PromptTemplateActivateRequest(version=2),
        ADMIN_CTX,
    )

    mock_clear_prompt_cache.assert_called_once_with("florence_soap")
    assert result["active_version"] == 2
