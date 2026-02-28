"""Testes das 6 MCP Tools — 6 testes."""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre.llm.qwen_client import QwenClient
from pierre.llm.url_fetcher import URLFetcher
from pierre.mcp.tools.analyze_text import handle_analyze_text
from pierre.mcp.tools.check_regulatory import handle_check_regulatory
from pierre.mcp.tools.search_medical_literature import handle_search_medical_literature
from pierre.mcp.tools.summarize_document import handle_summarize_document
from pierre.mcp.tools.translate_to_portuguese import handle_translate_to_portuguese
from pierre.mcp.tools.web_search import handle_web_search
from pierre.models import (
    LiteratureSearchResponse,
    MedicalArticle,
    RegulatoryResponse,
    RegulatoryResult,
    SearchStatus,
    SummaryResult,
    TextAnalysisResult,
    TranslationResult,
    WebSearchResponse,
    WebSearchResult,
)
from pierre.search.bireme_client import BIREMEClient
from pierre.search.pubmed_client import PubMedClient
from pierre.search.regulatory_client import RegulatoryClient
from pierre.search.scielo_client import SciELOClient
from pierre.search.tavily_client import TavilySearchClient


@pytest.mark.asyncio
async def test_tool_web_search():
    """web_search tool retorna resultado serializado."""
    mock_tavily = AsyncMock(spec=TavilySearchClient)
    mock_tavily.search.return_value = WebSearchResponse(
        status=SearchStatus.SUCCESS,
        results=[WebSearchResult(title="Test Result", url="https://test.com", content="Content")],
        answer="Test answer",
        total_results=1,
        query_time_ms=100,
    )

    result = await handle_web_search(mock_tavily, {"query": "test"})

    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["answer"] == "Test answer"


@pytest.mark.asyncio
async def test_tool_search_medical_literature():
    """search_medical_literature tool retorna artigos."""
    mock_pubmed = AsyncMock(spec=PubMedClient)
    mock_pubmed.search.return_value = LiteratureSearchResponse(
        status=SearchStatus.SUCCESS,
        articles=[MedicalArticle(title="Test Article", pmid="12345")],
        total_found=1,
        returned=1,
        database_used="pubmed",
        query_time_ms=200,
    )
    mock_bireme = AsyncMock(spec=BIREMEClient)
    mock_scielo = AsyncMock(spec=SciELOClient)

    result = await handle_search_medical_literature(
        mock_pubmed, mock_bireme, mock_scielo,
        {"query": "metformin CKD", "database": "pubmed"},
    )

    assert result["status"] == "success"
    assert len(result["articles"]) == 1
    assert result["articles"][0]["pmid"] == "12345"


@pytest.mark.asyncio
async def test_tool_search_medical_literature_with_knowledge():
    """search_medical_literature inclui contexto de conhecimento quando configurado."""
    mock_pubmed = AsyncMock(spec=PubMedClient)
    mock_pubmed.search.return_value = LiteratureSearchResponse(
        status=SearchStatus.SUCCESS,
        articles=[MedicalArticle(title="Test Article", pmid="12345")],
        total_found=1,
        returned=1,
        database_used="pubmed",
        query_time_ms=200,
    )
    mock_bireme = AsyncMock(spec=BIREMEClient)
    mock_scielo = AsyncMock(spec=SciELOClient)
    mock_knowledge = AsyncMock()
    mock_knowledge.query_rag.return_value = [{"id": "proto-1", "text": "contexto"}]

    result = await handle_search_medical_literature(
        mock_pubmed,
        mock_bireme,
        mock_scielo,
        {"query": "metformin CKD", "database": "pubmed"},
        knowledge_client=mock_knowledge,
    )

    assert result["status"] == "success"
    assert "knowledge_results" in result
    assert len(result["knowledge_results"]) == 1


@pytest.mark.asyncio
async def test_tool_check_regulatory():
    """check_regulatory tool retorna resultados regulatorios."""
    mock_regulatory = AsyncMock(spec=RegulatoryClient)
    mock_regulatory.check.return_value = RegulatoryResponse(
        status=SearchStatus.SUCCESS,
        results=[RegulatoryResult(title="Empagliflozina", authority="ANVISA", status="aprovado")],
        query_time_ms=150,
        source="tavily+web",
    )

    result = await handle_check_regulatory(
        mock_regulatory,
        {"query": "empagliflozina ANVISA"},
    )

    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["authority"] == "ANVISA"


@pytest.mark.asyncio
async def test_tool_analyze_text():
    """analyze_text tool retorna analise via LLM."""
    mock_qwen = AsyncMock(spec=QwenClient)
    mock_qwen.analyze.return_value = TextAnalysisResult(
        analysis="Analise do texto...",
        key_points=["Ponto 1", "Ponto 2"],
        confidence=0.85,
        model_used="qwen2.5:7b",
        processing_time_ms=500,
    )

    result = await handle_analyze_text(
        mock_qwen,
        {"text": "Texto medico...", "instruction": "Analise contraindicacoes"},
    )

    assert result["confidence"] == 0.85
    assert len(result["key_points"]) == 2


@pytest.mark.asyncio
async def test_tool_summarize_document():
    """summarize_document tool resume texto."""
    mock_qwen = AsyncMock(spec=QwenClient)
    mock_qwen.summarize.return_value = SummaryResult(
        summary="Resumo do guideline KDIGO...",
        key_actions=["Iniciar SGLT2i", "Monitorar potassio"],
        summary_type="clinical_action",
        processing_time_ms=400,
    )
    mock_fetcher = AsyncMock(spec=URLFetcher)

    result = await handle_summarize_document(
        mock_qwen, mock_fetcher,
        {"text": "Guideline completo...", "summary_type": "clinical_action"},
    )

    assert "Resumo" in result["summary"]
    assert len(result["key_actions"]) == 2


@pytest.mark.asyncio
async def test_tool_translate_to_portuguese():
    """translate_to_portuguese tool traduz texto."""
    mock_qwen = AsyncMock(spec=QwenClient)
    mock_qwen.translate.return_value = TranslationResult(
        translated_text="As diretrizes KDIGO 2024...",
        source_language_detected="en",
        medical_terms_preserved=["KDIGO", "SGLT2"],
        confidence=0.92,
        processing_time_ms=300,
    )

    result = await handle_translate_to_portuguese(
        mock_qwen,
        {"text": "The 2024 KDIGO guidelines..."},
    )

    assert "KDIGO" in result["translated_text"]
    assert result["confidence"] == 0.92
    assert "SGLT2" in result["medical_terms_preserved"]
