"""Testes para o indexador RAG."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from florence.engine.rag.indexer import ProtocolIndexer
from florence.engine.rag.models import Protocol


@pytest.fixture
def temp_protocols_dir():
    """Cria diretório temporário com protocolos de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        protocols_dir = Path(tmpdir) / "protocols"
        protocols_dir.mkdir()

        # Criar protocolo de teste
        protocol_content = """# Protocolo de Teste

**Especialidade**: Cardiologia  
**Versão**: 1.0  
**Data**: 2026-02-15  
**Fonte**: Teste

## Indicações

Este é um protocolo de teste para validar o indexador.

## Critérios Diagnósticos

Critérios de teste:
- Critério 1
- Critério 2

## Conduta

Conduta de teste.
"""
        protocol_file = protocols_dir / "teste.md"
        protocol_file.write_text(protocol_content, encoding="utf-8")

        yield protocols_dir


@pytest.fixture
def temp_chroma_dir():
    """Cria diretório temporário para ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "chroma"


@pytest.fixture
def indexer(temp_protocols_dir, temp_chroma_dir):
    """Cria indexer para testes."""
    return ProtocolIndexer(
        protocols_dir=temp_protocols_dir,
        chroma_persist_dir=temp_chroma_dir,
        collection_name="test_protocols",
        chunk_size=100,
        chunk_overlap=10,
    )


def test_load_protocol_from_file(indexer, temp_protocols_dir):
    """Testa carregamento de protocolo de arquivo."""
    protocol_file = temp_protocols_dir / "teste.md"
    protocol = indexer.load_protocol_from_file(protocol_file)

    assert protocol.id == "teste"
    assert protocol.title == "Protocolo de Teste"
    assert protocol.specialty == "Cardiologia"
    assert protocol.version == "1.0"
    assert "Indicações" in protocol.content


def test_extract_metadata(indexer):
    """Testa extração de metadados."""
    content = """# Teste de Metadados

**Especialidade**: Endocrinologia  
**Versão**: 2.0  
**Data**: 2026-02-15  
**Fonte**: Diretrizes SBD

Conteúdo do protocolo.
"""
    metadata = indexer._extract_metadata(content)

    assert metadata["title"] == "Teste de Metadados"
    assert metadata["specialty"] == "Endocrinologia"
    assert metadata["version"] == "2.0"
    assert metadata["source"] == "Diretrizes SBD"
    assert isinstance(metadata["date"], datetime)


def test_chunk_document(indexer):
    """Testa divisão de documento em chunks."""
    protocol = Protocol(
        id="test",
        title="Test Protocol",
        specialty="Test",
        content="# Test\n\n" + ("Test content. " * 100),  # Conteúdo longo
    )

    chunks = indexer.chunk_document(protocol)

    assert len(chunks) > 0
    assert all(chunk.protocol_id == "test" for chunk in chunks)
    assert all(chunk.chunk_id.startswith("test_chunk_") for chunk in chunks)
    assert all("title" in chunk.metadata for chunk in chunks)


def test_index_protocol(indexer, temp_protocols_dir):
    """Testa indexação de protocolo."""
    protocol_file = temp_protocols_dir / "teste.md"
    protocol = indexer.load_protocol_from_file(protocol_file)

    num_chunks = indexer.index_protocol(protocol)

    assert num_chunks > 0


def test_index_all_protocols(indexer):
    """Testa indexação de todos os protocolos."""
    results = indexer.index_all_protocols()

    assert len(results) > 0
    assert "teste" in results
    assert results["teste"] > 0


def test_list_indexed_protocols(indexer):
    """Testa listagem de protocolos indexados."""
    # Indexar primeiro
    indexer.index_all_protocols()

    protocols = indexer.list_indexed_protocols()

    assert len(protocols) > 0
    assert any(p["title"] == "Protocolo de Teste" for p in protocols)


def test_get_stats(indexer):
    """Testa estatísticas do índice."""
    # Indexar primeiro
    indexer.index_all_protocols()

    stats = indexer.get_stats()

    assert stats["total_protocols"] > 0
    assert stats["total_chunks"] > 0
    assert stats["avg_chunks_per_protocol"] > 0
    assert stats["collection_name"] == "test_protocols"


def test_clear_index(indexer):
    """Testa limpeza do índice."""
    # Indexar primeiro
    indexer.index_all_protocols()

    # Verificar que tem dados
    stats_before = indexer.get_stats()
    assert stats_before["total_chunks"] > 0

    # Limpar
    indexer.clear_index()

    # Verificar que está vazio
    stats_after = indexer.get_stats()
    assert stats_after["total_chunks"] == 0


def test_generate_chunk_id(indexer):
    """Testa geração de ID de chunk."""
    chunk_id = indexer._generate_chunk_id("diabetes", 5)

    assert chunk_id == "diabetes_chunk_005"

