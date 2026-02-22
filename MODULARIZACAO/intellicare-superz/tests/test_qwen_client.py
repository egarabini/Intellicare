"""Testes do QwenClient — 5 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from superz.llm.qwen_client import QwenClient


@pytest.mark.asyncio
async def test_qwen_analyze_success():
    """analyze() retorna TextAnalysisResult com key_points."""
    client = QwenClient(model="qwen2.5:7b", model_fallback="qwen2.5:7b")

    mock_response = httpx.Response(
        status_code=200,
        json={
            "message": {
                "content": "Com base no texto:\n- Ponto 1: Metformina contraindicada em eGFR < 30\n- Ponto 2: Monitorar a cada 3 meses\n- Ponto 3: Dose max 1000mg/dia para eGFR 45-60"
            }
        },
        request=httpx.Request("POST", "http://localhost:11434/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.analyze(
            text="Artigo sobre metformina em DRC...",
            instruction="Extraia contraindicacoes",
        )

    assert result.analysis != ""
    assert len(result.key_points) >= 2
    assert result.model_used == "qwen2.5:7b"
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_qwen_summarize_success():
    """summarize() retorna SummaryResult."""
    client = QwenClient(model="qwen2.5:7b", model_fallback="qwen2.5:7b")

    mock_response = httpx.Response(
        status_code=200,
        json={
            "message": {
                "content": "Resumo:\n- Iniciar SGLT2i para DRC com TFG >= 25\n- Monitorar potassio\n- IECA/BRA se ACR > 30"
            }
        },
        request=httpx.Request("POST", "http://localhost:11434/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.summarize(text="Guideline KDIGO 2024...")

    assert result.summary != ""
    assert len(result.key_actions) >= 2


@pytest.mark.asyncio
async def test_qwen_translate_success():
    """translate() retorna TranslationResult com termos preservados."""
    client = QwenClient(model="qwen2.5:7b", model_fallback="qwen2.5:7b")

    mock_response = httpx.Response(
        status_code=200,
        json={
            "message": {
                "content": "As diretrizes KDIGO 2024 recomendam inibidores de SGLT2 para DRC com eGFR >= 25."
            }
        },
        request=httpx.Request("POST", "http://localhost:11434/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.translate(
            text="The 2024 KDIGO guidelines recommend SGLT2 inhibitors for CKD with eGFR >= 25."
        )

    assert "KDIGO" in result.translated_text
    assert "SGLT2" in result.translated_text
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_qwen_unavailable_graceful_degradation():
    """Ollama indisponivel: analyze retorna erro estruturado em vez de crash."""
    client = QwenClient(
        ollama_url="http://localhost:99999",
        model="qwen2.5:72b",
        model_fallback="qwen2.5:7b",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=Exception("Connection refused")):
        result = await client.analyze(
            text="Texto de teste",
            instruction="Analise isso",
        )

    assert "[ERRO]" in result.analysis
    assert result.confidence == 0.0
    assert result.model_used == "none"


@pytest.mark.asyncio
async def test_qwen_fallback_model():
    """Modelo primario falha, usa fallback."""
    client = QwenClient(model="qwen2.5:72b", model_fallback="qwen2.5:7b")

    call_count = 0

    async def mock_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        body = kwargs.get("json", {})
        model = body.get("model", "")

        if model == "qwen2.5:72b":
            raise Exception("Model too large")

        # Fallback funciona
        return httpx.Response(
            status_code=200,
            json={"message": {"content": "Resultado do fallback 7B"}},
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
        )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=mock_post):
        result = await client.analyze(text="Teste", instruction="Analise")

    assert result.model_used == "qwen2.5:7b"
    assert "fallback" in result.analysis.lower() or result.analysis != ""
