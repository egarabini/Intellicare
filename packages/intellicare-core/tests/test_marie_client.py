from __future__ import annotations

from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from modules.marie.client import call_marie
from modules.oswaldo.contracts import OswaldoSuggestRequest
from modules.oswaldo.services import suggest as suggest_oswaldo


def _clear_settings_cache() -> None:
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_marie_disabled_uses_fallback(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "false")
    monkeypatch.delenv("MARIE_API_KEY", raising=False)
    _clear_settings_cache()

    fallback = AsyncMock(return_value={"source": "fallback"})

    with patch("modules.marie.client.httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        result = await call_marie("cid10_rag", {"query": "cefaleia"}, fallback_fn=fallback)

    assert result == {"source": "fallback"}
    post.assert_not_called()
    fallback.assert_awaited_once()


@pytest.mark.asyncio
async def test_marie_enabled_calls_dify(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    monkeypatch.setenv("MARIE_API_URL", "http://marie-api:5001")
    _clear_settings_cache()

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"answer": '{"cid10_code":"R51","cid10_desc":"Cefaleia"}'}

    with patch("modules.marie.client.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        result = await call_marie("cid10_rag", {"query": "cefaleia", "patient_history": "hist"})

    assert result["answer"]
    post.assert_awaited_once()


@pytest.mark.asyncio
async def test_marie_timeout_uses_fallback(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    _clear_settings_cache()

    fallback = AsyncMock(return_value={"source": "fallback"})

    with patch(
        "modules.marie.client.httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("timeout"),
    ):
        result = await call_marie("cid10_rag", {"query": "cefaleia"}, fallback_fn=fallback)

    assert result == {"source": "fallback"}
    fallback.assert_awaited_once()


@pytest.mark.asyncio
async def test_marie_5xx_uses_fallback(monkeypatch, caplog):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    _clear_settings_cache()

    request = httpx.Request("POST", "http://marie-api:5001/v1/chat-messages")
    response = httpx.Response(503, request=request)
    fallback = AsyncMock(return_value={"source": "fallback"})

    with patch(
        "modules.marie.client.httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=MagicMock(
            raise_for_status=MagicMock(side_effect=httpx.HTTPStatusError("boom", request=request, response=response))
        ),
    ):
        result = await call_marie("cid10_rag", {"query": "cefaleia"}, fallback_fn=fallback)

    assert result == {"source": "fallback"}
    assert "Marie unavailable" in caplog.text


@pytest.mark.asyncio
async def test_suggest_cid10_with_marie(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    _clear_settings_cache()

    captured: dict = {}

    async def fake_call_marie(workflow_slug: str, inputs: dict, fallback_fn=None):
        del fallback_fn
        captured["workflow_slug"] = workflow_slug
        captured["inputs"] = inputs
        return {"answer": '{"cid10_code":"R51","cid10_desc":"Cefaleia"}'}

    async def fake_local_suggestion(req: OswaldoSuggestRequest):
        del req
        return {
            "cid10_code": "Z00",
            "cid10_desc": "Consulta de rotina",
            "items": [{"drug": "Dipirona", "posology": "1 comp 8/8h", "duration": "3 dias"}],
            "model": "local-llm",
        }, "high"

    async def fake_timeline_summary(ctx: TenantContext, patient_id):
        del ctx, patient_id
        return "- Consulta: cefaleia recorrente [closed]"

    monkeypatch.setattr("modules.oswaldo.services.call_marie", fake_call_marie)
    monkeypatch.setattr("modules.oswaldo.services._local_suggestion", fake_local_suggestion)
    monkeypatch.setattr("modules.oswaldo.services._get_patient_timeline_summary", fake_timeline_summary)
    monkeypatch.setattr(
        "modules.oswaldo.services._coerce_patient_uuid",
        lambda patient_id: UUID("11111111-1111-1111-1111-111111111111"),
    )

    ctx = TenantContext.from_slug(
        slug="clinica_alfa",
        user_id="clinico-1",
        roles=["CLINICO"],
        email="clinico@test.local",
    )
    result = await suggest_oswaldo(
        ctx,
        OswaldoSuggestRequest(
            encounter_id=1,
            patient_id=1,
            chief_complaint="cefaleia intensa",
        ),
    )

    assert captured["workflow_slug"] == "cid10_rag"
    assert captured["inputs"]["query"] == "cefaleia intensa"
    assert "cefaleia recorrente" in captured["inputs"]["patient_history"]
    assert result.cid10_code == "R51"
    assert result.model == "marie"
    assert len(result.prescription_items) == 1
