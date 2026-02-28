"""Tests for ContradictionDetector (EF-W004)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from wanda.discovery.models import ModuleResponse
from wanda.llm.exceptions import LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMResponse
from wanda.orchestrator.contradiction_detector import Contradiction, ContradictionDetector


# ── Helpers ────────────────────────────────────────────────────────────────

def make_response(module_name: str, data: str = "Resposta normal") -> ModuleResponse:
    return ModuleResponse(
        module_name=module_name,
        endpoint="/api/v1/analyze",
        status_code=200,
        data={"data": data},
    )


def make_failed_response(module_name: str) -> ModuleResponse:
    return ModuleResponse(
        module_name=module_name,
        endpoint="/api/v1/analyze",
        status_code=500,
        data={},
        error="Timeout",
    )


def make_llm_response_no_contradictions() -> LLMResponse:
    return LLMResponse(
        content=json.dumps({
            "contradictions": [],
            "has_contradictions": False,
        }),
        model="llama3.1:8b",
    )


def make_llm_response_with_contradiction() -> LLMResponse:
    return LLMResponse(
        content=json.dumps({
            "contradictions": [
                {
                    "field": "DRC staging",
                    "agent_a": "intellicare-oswaldo",
                    "value_a": "G3a",
                    "agent_b": "intellicare-florence",
                    "value_b": "G4",
                    "severity": "error",
                    "description": "Estadiamento DRC divergente entre agentes",
                }
            ],
            "has_contradictions": True,
        }),
        model="llama3.1:8b",
    )


# ── Tests ──────────────────────────────────────────────────────────────────

class TestContradictionDetector:
    @pytest.mark.asyncio
    async def test_no_contradiction_detected(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response_no_contradictions())
        detector = ContradictionDetector(llm_provider=llm_mock)

        responses = [
            make_response("intellicare-oswaldo", "DRC G3a"),
            make_response("intellicare-florence", "DRC G3a estavel"),
        ]
        contradictions = await detector.detect(responses)
        assert contradictions == []

    @pytest.mark.asyncio
    async def test_contradiction_detected(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(return_value=make_llm_response_with_contradiction())
        detector = ContradictionDetector(llm_provider=llm_mock)

        responses = [
            make_response("intellicare-oswaldo", "DRC G3a"),
            make_response("intellicare-florence", "DRC G4 — progressao"),
        ]
        contradictions = await detector.detect(responses)

        assert len(contradictions) == 1
        assert contradictions[0].field == "DRC staging"
        assert contradictions[0].severity == "error"
        assert contradictions[0].agent_a == "intellicare-oswaldo"

    @pytest.mark.asyncio
    async def test_single_response_returns_empty(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock()
        detector = ContradictionDetector(llm_provider=llm_mock)

        responses = [make_response("intellicare-oswaldo")]
        contradictions = await detector.detect(responses)

        assert contradictions == []
        llm_mock.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_responses_excluded(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock()
        detector = ContradictionDetector(llm_provider=llm_mock)

        # Only 1 successful response + 1 failed → should not call LLM
        responses = [
            make_response("intellicare-oswaldo"),
            make_failed_response("intellicare-florence"),
        ]
        contradictions = await detector.detect(responses)

        assert contradictions == []
        llm_mock.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_graceful_on_llm_unavailable(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMUnavailableError("http://localhost:11434"))
        detector = ContradictionDetector(llm_provider=llm_mock)

        responses = [
            make_response("intellicare-oswaldo"),
            make_response("intellicare-florence"),
        ]
        contradictions = await detector.detect(responses)

        # Should return empty (graceful degradation)
        assert contradictions == []

    @pytest.mark.asyncio
    async def test_graceful_on_llm_timeout(self):
        llm_mock = MagicMock()
        llm_mock.chat = AsyncMock(side_effect=LLMTimeoutError(timeout_seconds=5.0))
        detector = ContradictionDetector(llm_provider=llm_mock)

        responses = [
            make_response("intellicare-oswaldo"),
            make_response("intellicare-florence"),
        ]
        contradictions = await detector.detect(responses)
        assert contradictions == []
