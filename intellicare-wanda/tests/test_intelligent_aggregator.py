"""Tests for IntelligentAggregator (EF-W004) — LLM-based response synthesis."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from wanda.discovery.models import ModuleResponse, RoutingDecision
from wanda.llm.exceptions import LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMResponse
from wanda.orchestrator.aggregator import ResponseAggregator
from wanda.orchestrator.intelligent_aggregator import IntelligentAggregator


# ── Helpers ────────────────────────────────────────────────────────────────

def make_module_response(module_name: str, data: dict = None, success: bool = True) -> ModuleResponse:
    return ModuleResponse(
        module_name=module_name,
        endpoint="/api/v1/analyze",
        status_code=200 if success else 500,
        data=data or {"data": f"Resposta do {module_name}"},
        error="" if success else "Timeout",
    )


def make_llm_synthesis_response(synthesis: str = "Sintese do LLM") -> LLMResponse:
    return LLMResponse(
        content=json.dumps({
            "synthesis": synthesis,
            "key_points": ["Ponto 1", "Ponto 2"],
            "recommended_actions": ["Acao 1"],
            "critical_alerts": [],
            "data_sources": {"intellicare-oswaldo": "Dados de DRC"},
            "confidence": 0.9,
        }),
        model="llama3.1:8b",
        latency_ms=200,
    )


def make_aggregator(llm_mock):
    simple = ResponseAggregator()
    return IntelligentAggregator(
        llm_provider=llm_mock,
        simple_aggregator=simple,
        max_agents_for_llm=5,
    )


# ── Tests: Single Agent Pass-Through ──────────────────────────────────────

class TestSingleAgentPassThrough:
    @pytest.mark.asyncio
    async def test_single_success_uses_simple(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock()
        agg = make_aggregator(llm_mock)

        responses = [make_module_response("intellicare-oswaldo")]
        result = await agg.aggregate(query="Pergunta simples", responses=responses)

        # LLM should NOT be called for single agent
        llm_mock.chat.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_success_uses_simple(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock()
        agg = make_aggregator(llm_mock)

        responses = [make_module_response("intellicare-oswaldo", success=False)]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        llm_mock.chat.assert_not_called()
        assert result is not None


# ── Tests: Multi-Agent LLM Aggregation ────────────────────────────────────

class TestMultiAgentLLMAggregation:
    @pytest.mark.asyncio
    async def test_two_agents_use_llm(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response(
            "DRC G3a estavel. Laboratorio normal."
        ))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(query="Como esta o paciente?", responses=responses)

        llm_mock.chat.assert_awaited_once()
        assert "DRC G3a" in result.aggregated_response

    @pytest.mark.asyncio
    async def test_three_agents_synthesized(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response(
            "Resultado multi-agente"
        ))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
            make_module_response("intellicare-geralda"),
        ]
        result = await agg.aggregate(
            query="Como esta o paciente?",
            responses=responses,
            routing=RoutingDecision(
                target_modules=["intellicare-oswaldo", "intellicare-florence", "intellicare-geralda"],
                reason="multi",
            ),
        )

        assert result.modules_used is not None

    @pytest.mark.asyncio
    async def test_modules_used_excludes_failures(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response())
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
            make_module_response("intellicare-zilda", success=False),
        ]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        assert "intellicare-oswaldo" in result.modules_used
        assert "intellicare-zilda" not in result.modules_used


# ── Tests: Recipient Types ─────────────────────────────────────────────────

class TestRecipientTypes:
    @pytest.mark.asyncio
    async def test_professional_recipient(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response(
            "**DRC G3a** — TFG 45. Pressao necessita controle."
        ))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(
            query="Avaliacao clinica",
            responses=responses,
            recipient_type="professional",
        )

        # Verify LLM was called (professional prompt)
        llm_mock.chat.assert_awaited_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_patient_recipient(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response(
            "Seus exames estao bem! Continue tomando os medicamentos."
        ))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-geralda"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(
            query="Como estou?",
            responses=responses,
            recipient_type="patient",
        )

        llm_mock.chat.assert_awaited_once()
        assert result is not None


# ── Tests: Fallback ────────────────────────────────────────────────────────

class TestFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_llm_unavailable(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMUnavailableError("http://localhost:11434"))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        # Should still return a result (simple fallback)
        assert result is not None
        assert result.aggregated_response != ""

    @pytest.mark.asyncio
    async def test_fallback_on_llm_timeout(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMTimeoutError(timeout_seconds=15.0))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        assert result is not None

    @pytest.mark.asyncio
    async def test_fallback_on_empty_synthesis(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=LLMResponse(
            content=json.dumps({"synthesis": "", "key_points": []}),
            model="llama3.1:8b",
        ))
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        # Empty synthesis triggers fallback
        assert result is not None

    @pytest.mark.asyncio
    async def test_fallback_for_too_many_agents(self):
        """When agents exceed max_agents_for_llm, use simple aggregation."""
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock()
        agg = IntelligentAggregator(
            llm_provider=llm_mock,
            simple_aggregator=ResponseAggregator(),
            max_agents_for_llm=2,  # Very low limit
        )

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
            make_module_response("intellicare-geralda"),
            make_module_response("intellicare-zilda"),
        ]
        result = await agg.aggregate(query="Pergunta", responses=responses)

        # 4 agents > max_agents_for_llm=2 → simple fallback, no LLM call
        llm_mock.chat.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_safety_warnings_propagated(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_synthesis_response())
        agg = make_aggregator(llm_mock)

        responses = [
            make_module_response("intellicare-oswaldo"),
            make_module_response("intellicare-florence"),
        ]
        warnings = ["IPS-First: paciente sem contexto carregado"]
        result = await agg.aggregate(
            query="Pergunta",
            responses=responses,
            safety_warnings=warnings,
        )

        assert "IPS-First" in result.safety_warnings[0]
