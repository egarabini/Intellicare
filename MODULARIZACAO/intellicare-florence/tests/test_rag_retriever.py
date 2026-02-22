"""Testes para o retriever RAG."""

import tempfile
from pathlib import Path

import pytest

from florence.engine.rag.indexer import ProtocolIndexer
from florence.engine.rag.models import RAGQuery
from florence.engine.rag.retriever import ProtocolRetriever


@pytest.fixture
def temp_protocols_dir():
    """Cria diretório temporário com protocolos de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        protocols_dir = Path(tmpdir) / "protocols"
        protocols_dir.mkdir()

        # Criar 2 protocolos de teste
        protocol1 = """# Diabetes Mellitus

**Especialidade**: Endocrinologia  
**Versão**: 1.0  
**Data**: 2026-02-15  
**Fonte**: SBD

## Indicações

Pacientes com glicemia elevada.

## Critérios Diagnósticos

Glicemia de jejum >= 126 mg/dL ou HbA1c >= 6.5%.

## Conduta

Metformina 500-2000 mg/dia.
"""

        protocol2 = """# Hipertensão Arterial

**Especialidade**: Cardiologia  
**Versão**: 1.0  
**Data**: 2026-02-15  
**Fonte**: SBC

## Indicações

Pacientes com pressão arterial elevada.

## Critérios Diagnósticos

PA >= 140/90 mmHg.

## Conduta

IECA ou BRA como primeira linha.
"""

        (protocols_dir / "diabetes.md").write_text(protocol1, encoding="utf-8")
        (protocols_dir / "hipertensao.md").write_text(protocol2, encoding="utf-8")

        yield protocols_dir


@pytest.fixture
def temp_chroma_dir():
    """Cria diretório temporário para ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "chroma"


@pytest.fixture
def indexed_retriever(temp_protocols_dir, temp_chroma_dir):
    """Cria retriever com protocolos já indexados."""
    # Indexar protocolos
    indexer = ProtocolIndexer(
        protocols_dir=temp_protocols_dir,
        chroma_persist_dir=temp_chroma_dir,
        collection_name="test_protocols",
    )
    indexer.index_all_protocols()

    # Criar retriever
    retriever = ProtocolRetriever(
        chroma_persist_dir=str(temp_chroma_dir),
        collection_name="test_protocols",
    )

    return retriever


def test_retrieve_basic(indexed_retriever):
    """Testa busca básica."""
    results = indexed_retriever.retrieve(
        query="Como tratar diabetes?",
        top_k=2,
    )

    assert len(results) > 0
    assert all(hasattr(r, "title") for r in results)
    assert all(hasattr(r, "score") for r in results)
    assert all(0 <= r.score <= 1 for r in results)


def test_retrieve_with_filters(indexed_retriever):
    """Testa busca com filtros."""
    results = indexed_retriever.retrieve(
        query="tratamento",
        top_k=5,
        filters={"specialty": "Endocrinologia"},
    )

    # Deve retornar apenas protocolos de Endocrinologia
    assert len(results) > 0
    # Verificar que todos são da especialidade correta
    for result in results:
        assert result.metadata.get("specialty") == "Endocrinologia"


def test_query_rag(indexed_retriever):
    """Testa query RAG completa."""
    query = RAGQuery(
        query="Qual a meta de glicemia?",
        top_k=3,
    )

    response = indexed_retriever.query(query)

    assert response.query == query.query
    assert response.total_results > 0
    assert response.execution_time_ms > 0
    assert len(response.results) > 0


def test_search_by_specialty(indexed_retriever):
    """Testa busca por especialidade."""
    results = indexed_retriever.search_by_specialty(
        specialty="Cardiologia",
        top_k=5,
    )

    assert len(results) > 0
    # Verificar que todos são de Cardiologia
    for result in results:
        assert result.metadata.get("specialty") == "Cardiologia"


def test_retrieve_top_k(indexed_retriever):
    """Testa limite de resultados (top_k)."""
    results = indexed_retriever.retrieve(
        query="tratamento",
        top_k=1,
    )

    assert len(results) <= 1


def test_retrieve_empty_query(indexed_retriever):
    """Testa query vazia."""
    results = indexed_retriever.retrieve(
        query="",
        top_k=3,
    )

    # Deve retornar resultados mesmo com query vazia
    assert isinstance(results, list)


def test_score_ordering(indexed_retriever):
    """Testa ordenação por score."""
    results = indexed_retriever.retrieve(
        query="diabetes glicemia HbA1c",
        top_k=5,
    )

    if len(results) > 1:
        # Verificar que está ordenado por score (decrescente)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


def test_query_response_structure(indexed_retriever):
    """Testa estrutura da resposta."""
    query = RAGQuery(query="teste", top_k=2)
    response = indexed_retriever.query(query)

    assert hasattr(response, "query")
    assert hasattr(response, "results")
    assert hasattr(response, "total_results")
    assert hasattr(response, "execution_time_ms")
    assert isinstance(response.results, list)
    assert isinstance(response.total_results, int)
    assert isinstance(response.execution_time_ms, float)

