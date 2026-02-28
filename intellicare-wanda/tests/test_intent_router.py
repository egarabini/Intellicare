"""Tests for IntentRouter (EF-W003) — LLM-based routing with keyword fallback."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMResponse
from wanda.orchestrator.intent_router import IntentRouter
from wanda.orchestrator.router import QueryRouter


# ── Helpers ────────────────────────────────────────────────────────────────

def make_module(name, caps=None):
    return ModuleInfo(
        name=name,
        base_url=f"http://localhost:8001",
        version="1.0.0",
        capabilities=caps or ["general"],
        status=ModuleStatus.ONLINE,
    )


def make_llm_response(content: str, latency_ms: int = 50) -> LLMResponse:
    return LLMResponse(content=content, model="llama3.1:8b", latency_ms=latency_ms)


def make_router(llm_mock):
    keyword_router = QueryRouter(max_modules=3)
    return IntentRouter(
        llm_provider=llm_mock,
        keyword_router=keyword_router,
        confidence_min=0.7,
    )


ONLINE_MODULES = [
    make_module("intellicare-oswaldo", ["chronic-disease-monitoring"]),
    make_module("intellicare-florence", ["lab-interpretation", "clinical-analysis"]),
    make_module("intellicare-geralda", ["care-plans", "reminders"]),
    make_module("intellicare-zilda", ["cnes-data"]),
]


# ── Tests: LLM Routing ─────────────────────────────────────────────────────

class TestLLMRoutingSuccess:
    @pytest.mark.asyncio
    async def test_single_agent_routing(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-oswaldo"],
                "secondary_agents": [],
                "reasoning": "Pergunta sobre DRC — Oswaldo especialista",
                "confidence": 0.92,
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="Como esta a creatinina do paciente com DRC?",
            available_modules=ONLINE_MODULES,
        )

        assert "intellicare-oswaldo" in decision.target_modules
        assert decision.routing_method == "llm"
        assert decision.confidence == 0.92
        llm_mock.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_multi_agent_routing(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-oswaldo", "intellicare-florence"],
                "secondary_agents": [],
                "reasoning": "TFG e exames laboratoriais — dois agentes",
                "confidence": 0.88,
                "multi_agent": True,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="TFG caiu — ver exames e estadiamento DRC",
            available_modules=ONLINE_MODULES,
        )

        assert "intellicare-oswaldo" in decision.target_modules
        assert "intellicare-florence" in decision.target_modules
        assert decision.routing_method == "llm"

    @pytest.mark.asyncio
    async def test_reasoning_propagated(self):
        expected_reason = "Pergunta sobre cuidado e adesao — Geralda"
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-geralda"],
                "secondary_agents": [],
                "reasoning": expected_reason,
                "confidence": 0.85,
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="Como esta a adesao do paciente?",
            available_modules=ONLINE_MODULES,
        )

        assert expected_reason in decision.reason

    @pytest.mark.asyncio
    async def test_patient_context_used(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-geralda"],
                "secondary_agents": [],
                "reasoning": "contexto do paciente",
                "confidence": 0.9,
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        await router.route(
            query="Como posso ajudar?",
            available_modules=ONLINE_MODULES,
            patient_id="P001",
            patient_context="Paciente com DRC G3, DM2",
        )

        # Verify LLM was called (patient context passed to prompt)
        llm_mock.chat.assert_awaited_once()


# ── Tests: LLM Fallback ────────────────────────────────────────────────────

class TestLLMFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_llm_unavailable(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMUnavailableError("http://localhost:11434"))
        router = make_router(llm_mock)

        decision = await router.route(
            query="Como esta o diabetes do paciente?",
            available_modules=ONLINE_MODULES,
        )

        # Should still route (keyword fallback)
        assert decision.routing_method == "keyword"
        assert len(decision.target_modules) > 0

    @pytest.mark.asyncio
    async def test_fallback_on_llm_timeout(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMTimeoutError(timeout_seconds=5.0))
        router = make_router(llm_mock)

        decision = await router.route(
            query="Plano de cuidado do paciente",
            available_modules=ONLINE_MODULES,
        )

        assert decision.routing_method == "keyword"

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            "Isso nao e JSON valido {{{ }"
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="exames de laboratorio",
            available_modules=ONLINE_MODULES,
        )

        assert decision.routing_method == "keyword"

    @pytest.mark.asyncio
    async def test_fallback_when_confidence_too_low(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-oswaldo"],
                "secondary_agents": [],
                "reasoning": "incerto",
                "confidence": 0.4,   # Below threshold of 0.7
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="nao sei bem o que perguntar",
            available_modules=ONLINE_MODULES,
        )

        assert decision.routing_method == "keyword"

    @pytest.mark.asyncio
    async def test_fallback_when_agents_not_in_available(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-invented-agent"],
                "secondary_agents": [],
                "reasoning": "agente inventado",
                "confidence": 0.95,
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="alguma pergunta",
            available_modules=ONLINE_MODULES,
        )

        # LLM returned non-existent agent — should fallback
        assert decision.routing_method == "keyword"

    @pytest.mark.asyncio
    async def test_fallback_on_generic_exception(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        router = make_router(llm_mock)

        decision = await router.route(
            query="alguma pergunta",
            available_modules=ONLINE_MODULES,
        )

        assert decision.routing_method == "keyword"

    @pytest.mark.asyncio
    async def test_fallback_when_primary_agents_missing(self):
        """LLM returns valid JSON but without the required 'primary_agents' key."""
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "agents": ["intellicare-oswaldo"],  # wrong key — should be "primary_agents"
                "confidence": 0.9,
                "reasoning": "DM2",
                "multi_agent": False,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="diabetes mellitus",
            available_modules=ONLINE_MODULES,
        )

        # Should fall back to keyword routing due to missing required field
        assert decision.routing_method == "keyword"


# ── Tests: Edge Cases ──────────────────────────────────────────────────────

class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_available_modules(self):
        llm_mock = MagicMock()
        router = make_router(llm_mock)

        decision = await router.route(
            query="alguma pergunta",
            available_modules=[],
        )

        assert decision.target_modules == []
        llm_mock.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_max_modules_respected(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": [
                    "intellicare-oswaldo",
                    "intellicare-florence",
                    "intellicare-geralda",
                    "intellicare-zilda",  # 4 agents — should be trimmed to max_modules=3
                ],
                "secondary_agents": [],
                "reasoning": "muitos agentes",
                "confidence": 0.9,
                "multi_agent": True,
            })
        ))
        router = IntentRouter(
            llm_provider=llm_mock,
            keyword_router=QueryRouter(max_modules=3),
            confidence_min=0.7,
            max_modules=3,
        )

        decision = await router.route(
            query="pergunta complexa",
            available_modules=ONLINE_MODULES,
        )

        assert len(decision.target_modules) <= 3

    @pytest.mark.asyncio
    async def test_secondary_agents_included_within_limit(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response(
            json.dumps({
                "primary_agents": ["intellicare-oswaldo"],
                "secondary_agents": ["intellicare-florence"],
                "reasoning": "primario + secundario",
                "confidence": 0.87,
                "multi_agent": True,
            })
        ))
        router = make_router(llm_mock)

        decision = await router.route(
            query="DRC e laboratorio",
            available_modules=ONLINE_MODULES,
        )

        assert "intellicare-oswaldo" in decision.target_modules
        assert "intellicare-florence" in decision.target_modules
