"""Testes unitarios do modulo SLM."""
from __future__ import annotations

import pytest

from modules.slm.schemas import AskRequest, AskResponse, ModelInfo, SourceRef
from modules.slm.service import _build_prompt, SYSTEM_PROMPT, SLM_MODEL


# ------------------------------------------------------------------
# AskRequest validation
# ------------------------------------------------------------------

def test_ask_request_defaults():
    r = AskRequest(query="Qual o protocolo de triagem?")
    assert r.limit == 5
    assert r.min_similarity == 0.5
    assert r.stream is False


def test_ask_request_custom():
    r = AskRequest(query="Hipertensão", limit=10, min_similarity=0.7, stream=True)
    assert r.limit == 10
    assert r.min_similarity == 0.7
    assert r.stream is True


def test_ask_request_query_too_short():
    with pytest.raises(ValueError):
        AskRequest(query="ab")


def test_ask_request_limit_bounds():
    with pytest.raises(ValueError):
        AskRequest(query="teste", limit=0)
    with pytest.raises(ValueError):
        AskRequest(query="teste", limit=21)


def test_ask_request_similarity_bounds():
    with pytest.raises(ValueError):
        AskRequest(query="teste", min_similarity=-0.1)
    with pytest.raises(ValueError):
        AskRequest(query="teste", min_similarity=1.1)


# ------------------------------------------------------------------
# Response models
# ------------------------------------------------------------------

def test_source_ref():
    s = SourceRef(title="Protocolo HAS", source_path="protocolos/has.pdf", similarity=0.87)
    assert s.title == "Protocolo HAS"
    assert s.similarity == 0.87


def test_ask_response():
    r = AskResponse(
        answer="Resposta gerada",
        sources=[SourceRef(title="Doc", source_path="doc.pdf", similarity=0.9)],
        model="llama3.2:3b",
        latency_ms=1200,
    )
    assert r.latency_ms == 1200
    assert len(r.sources) == 1


def test_model_info():
    m = ModelInfo(name="llama3.2:3b", size="2.0 GB")
    assert m.name == "llama3.2:3b"
    assert m.size == "2.0 GB"


def test_model_info_no_size():
    m = ModelInfo(name="phi4-mini")
    assert m.size is None


# ------------------------------------------------------------------
# _build_prompt
# ------------------------------------------------------------------

def test_build_prompt_single_chunk():
    chunks = [{"title": "Protocolo HAS", "content": "Texto do protocolo..."}]
    prompt = _build_prompt("Qual o protocolo?", chunks)
    assert "CONTEXTO:" in prompt
    assert "[Protocolo HAS]" in prompt
    assert "PERGUNTA: Qual o protocolo?" in prompt
    assert "RESPOSTA:" in prompt


def test_build_prompt_multiple_chunks():
    chunks = [
        {"title": "Doc A", "content": "Conteudo A"},
        {"title": "Doc B", "content": "Conteudo B"},
    ]
    prompt = _build_prompt("Pergunta?", chunks)
    assert "[Doc A]" in prompt
    assert "[Doc B]" in prompt
    assert "---" in prompt


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

def test_system_prompt_contains_key_instructions():
    assert "português do Brasil" in SYSTEM_PROMPT
    assert "Nunca invente" in SYSTEM_PROMPT
    assert "APENAS" in SYSTEM_PROMPT


def test_default_model():
    assert SLM_MODEL == "llama3.2:3b"

