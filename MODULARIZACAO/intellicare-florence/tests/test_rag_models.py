"""Testes dos modelos RAG."""

import pytest
from datetime import datetime

# Import direto dos modelos sem passar pelo __init__ que importa chromadb
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar apenas os modelos
try:
    from florence.engine.rag.models import (
        Protocol,
        ProtocolChunk,
        RAGQuery,
        RAGResult,
        RAGQueryResponse,
    )
except ImportError:
    pytest.skip("RAG dependencies not installed", allow_module_level=True)


class TestProtocolModel:
    """Testes do modelo Protocol."""

    def test_protocol_creation(self):
        """Criar protocolo."""
        protocol = Protocol(
            id="diabetes_tipo2",
            title="Manejo de Diabetes Mellitus Tipo 2",
            content="# Diabetes Tipo 2\n\nConteúdo do protocolo...",
            metadata={
                "specialty": "Endocrinologia",
                "version": "1.0",
                "date": "2024-01-15",
            },
        )

        assert protocol.id == "diabetes_tipo2"
        assert protocol.title == "Manejo de Diabetes Mellitus Tipo 2"
        assert "Diabetes Tipo 2" in protocol.content
        assert protocol.metadata["specialty"] == "Endocrinologia"

    def test_protocol_to_dict(self):
        """Serializar protocolo."""
        protocol = Protocol(
            id="test",
            title="Test Protocol",
            content="Content",
            metadata={"key": "value"},
        )

        data = protocol.to_dict()
        assert data["id"] == "test"
        assert data["title"] == "Test Protocol"
        assert data["content"] == "Content"
        assert data["metadata"]["key"] == "value"


class TestProtocolChunkModel:
    """Testes do modelo ProtocolChunk."""

    def test_chunk_creation(self):
        """Criar chunk de protocolo."""
        chunk = ProtocolChunk(
            protocol_id="diabetes_tipo2",
            chunk_index=0,
            content="Conteúdo do chunk...",
            metadata={
                "title": "Diabetes Tipo 2",
                "section": "Indicações",
            },
        )

        assert chunk.protocol_id == "diabetes_tipo2"
        assert chunk.chunk_index == 0
        assert "Conteúdo" in chunk.content
        assert chunk.metadata["section"] == "Indicações"

    def test_chunk_to_dict(self):
        """Serializar chunk."""
        chunk = ProtocolChunk(
            protocol_id="test",
            chunk_index=1,
            content="Test content",
            metadata={},
        )

        data = chunk.to_dict()
        assert data["protocol_id"] == "test"
        assert data["chunk_index"] == 1
        assert data["content"] == "Test content"


class TestRAGQueryModel:
    """Testes do modelo RAGQuery."""

    def test_query_creation(self):
        """Criar query RAG."""
        query = RAGQuery(
            query="Como interpretar creatinina elevada?",
            top_k=3,
            filters={"specialty": "Nefrologia"},
        )

        assert query.query == "Como interpretar creatinina elevada?"
        assert query.top_k == 3
        assert query.filters["specialty"] == "Nefrologia"

    def test_query_default_values(self):
        """Valores padrão da query."""
        query = RAGQuery(query="test")

        assert query.query == "test"
        assert query.top_k == 3
        assert query.filters is None

    def test_query_to_dict(self):
        """Serializar query."""
        query = RAGQuery(
            query="test query",
            top_k=5,
            filters={"key": "value"},
        )

        data = query.to_dict()
        assert data["query"] == "test query"
        assert data["top_k"] == 5
        assert data["filters"]["key"] == "value"


class TestRAGResultModel:
    """Testes do modelo RAGResult."""

    def test_result_creation(self):
        """Criar resultado RAG."""
        result = RAGResult(
            protocol_id="diabetes_tipo2",
            title="Diabetes Tipo 2",
            content="Conteúdo relevante...",
            score=0.95,
            metadata={"specialty": "Endocrinologia"},
        )

        assert result.protocol_id == "diabetes_tipo2"
        assert result.title == "Diabetes Tipo 2"
        assert result.score == 0.95
        assert result.metadata["specialty"] == "Endocrinologia"

    def test_result_to_dict(self):
        """Serializar resultado."""
        result = RAGResult(
            protocol_id="test",
            title="Test",
            content="Content",
            score=0.8,
            metadata={},
        )

        data = result.to_dict()
        assert data["protocol_id"] == "test"
        assert data["title"] == "Test"
        assert data["score"] == 0.8


class TestRAGQueryResponseModel:
    """Testes do modelo RAGQueryResponse."""

    def test_response_creation(self):
        """Criar resposta de query."""
        results = [
            RAGResult(
                protocol_id="p1",
                title="Protocol 1",
                content="Content 1",
                score=0.95,
                metadata={},
            ),
            RAGResult(
                protocol_id="p2",
                title="Protocol 2",
                content="Content 2",
                score=0.85,
                metadata={},
            ),
        ]

        response = RAGQueryResponse(
            query="test query",
            results=results,
            total_results=2,
            execution_time_ms=45.2,
        )

        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.execution_time_ms == 45.2

    def test_response_to_dict(self):
        """Serializar resposta."""
        results = [
            RAGResult(
                protocol_id="p1",
                title="P1",
                content="C1",
                score=0.9,
                metadata={},
            )
        ]

        response = RAGQueryResponse(
            query="test",
            results=results,
            total_results=1,
            execution_time_ms=10.0,
        )

        data = response.to_dict()
        assert data["query"] == "test"
        assert len(data["results"]) == 1
        assert data["total_results"] == 1
        assert data["execution_time_ms"] == 10.0

