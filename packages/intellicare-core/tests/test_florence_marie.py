from __future__ import annotations

from uuid import UUID

import pytest

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from modules.florence.contracts import SuggestRequest
from modules.florence.services import suggest_soap, _get_florence_timeline_context


def _clear_settings_cache() -> None:
    get_settings.cache_clear()


def _ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="clinica_alfa",
        user_id="clinico-1",
        roles=["CLINICO"],
        email="clinico@test.local",
    )


@pytest.mark.asyncio
async def test_florence_marie_disabled_uses_local_llm(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "false")
    _clear_settings_cache()

    async def fake_local_suggestion(req: SuggestRequest):
        del req
        return {"S": "S", "O": "O", "A": "A", "P": "P", "model": "local-llm"}, "high"

    monkeypatch.setattr("modules.florence.services._local_suggestion", fake_local_suggestion)

    result = await suggest_soap(
        _ctx(),
        SuggestRequest(encounter_id=1, patient_id=1, chief_complaint="cefaleia"),
    )

    assert result.model == "local-llm"
    assert result.soap_a == "A"


@pytest.mark.asyncio
async def test_florence_marie_enabled_sends_timeline_context(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    _clear_settings_cache()

    captured: dict = {}

    async def fake_call_marie(workflow_slug: str, inputs: dict, fallback_fn=None):
        del fallback_fn
        captured["workflow_slug"] = workflow_slug
        captured["inputs"] = inputs
        return {"answer": '{"soap_s":"S","soap_o":"O","soap_a":"A","soap_p":"P"}'}

    async def fake_context(ctx: TenantContext, patient_id: str | int, days: int = 180):
        del ctx, patient_id, days
        return "[2026-03-20] Consulta: Cefaleia recorrente"

    monkeypatch.setattr("modules.florence.services.call_marie", fake_call_marie)
    monkeypatch.setattr("modules.florence.services._get_florence_timeline_context", fake_context)

    result = await suggest_soap(
        _ctx(),
        SuggestRequest(encounter_id=1, patient_id=1, chief_complaint="cefaleia intensa"),
    )

    assert captured["workflow_slug"] == "florence_soap_rag"
    assert "Cefaleia recorrente" in captured["inputs"]["patient_history"]
    assert result.model == "marie"
    assert result.soap_p == "P"


@pytest.mark.asyncio
async def test_florence_marie_timeout_fallback(monkeypatch):
    monkeypatch.setenv("MARIE_ENABLED", "true")
    monkeypatch.setenv("MARIE_API_KEY", "secret")
    _clear_settings_cache()

    async def fake_call_marie(workflow_slug: str, inputs: dict, fallback_fn=None):
        del workflow_slug, inputs, fallback_fn
        return None

    async def fake_local_suggestion(req: SuggestRequest):
        del req
        return {"S": "local", "O": "O", "A": "A", "P": "P", "model": "local-llm"}, "high"

    monkeypatch.setattr("modules.florence.services.call_marie", fake_call_marie)
    monkeypatch.setattr("modules.florence.services._local_suggestion", fake_local_suggestion)

    result = await suggest_soap(
        _ctx(),
        SuggestRequest(encounter_id=1, patient_id=1, chief_complaint="cefaleia"),
    )

    assert result.model == "local-llm"
    assert result.soap_s == "local"


@pytest.mark.asyncio
async def test_florence_timeline_context_truncated(monkeypatch):
    class FakeTimelineService:
        async def clinical_timeline(self, ctx: TenantContext, patient_id: UUID, limit: int = 20, offset: int = 0):
            del ctx, patient_id, limit, offset
            items = []
            for idx in range(50):
                items.append({
                    "event_type": "clinical_note",
                    "title": f"Nota {idx}",
                    "subtitle": "x" * 200,
                    "metadata": {},
                    "occurred_at": f"2026-03-{idx % 28 + 1:02d}T10:00:00",
                })
            return {"items": items}

    monkeypatch.setattr("modules.florence.services._CUIDADO_SERVICE", FakeTimelineService())

    context = await _get_florence_timeline_context(
        _ctx(),
        "11111111-1111-1111-1111-111111111111",
    )

    assert len(context) == 3000
