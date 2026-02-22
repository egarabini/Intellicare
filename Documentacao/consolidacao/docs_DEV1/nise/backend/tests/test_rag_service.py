"""
============================================================================
NISE TRAINING MODULE - RAG SERVICE TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: RAG Service Tests
Versão: 1.0
Data: 25/03/2026
Responsável: DEV1
============================================================================
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.rag_service import RAGService, rag_service
from app.services.knowledge_base import (
    get_resource_documentation,
    get_loinc_code_info,
    search_knowledge_base
)

# ============================================================================
# KNOWLEDGE BASE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_resource_documentation():
    """Test getting resource documentation."""
    # Test Patient resource
    doc = await get_resource_documentation("Patient")
    assert doc is not None
    assert doc["description"]
    assert "resourceType" in doc["required_fields"]
    assert "name" in doc["required_fields"]
    
    # Test unknown resource
    doc = await get_resource_documentation("UnknownResource")
    assert doc is None


@pytest.mark.asyncio
async def test_get_loinc_code_info():
    """Test getting LOINC code information."""
    # Test glucose code
    info = await get_loinc_code_info("2339-0")
    assert info is not None
    assert info["code"] == "2339-0"
    assert "Glucose" in info["display"]
    assert info["reference_range"] is not None
    
    # Test unknown code
    info = await get_loinc_code_info("99999-9")
    assert info is None


@pytest.mark.asyncio
async def test_search_knowledge_base():
    """Test searching knowledge base."""
    # Search for Patient
    results = await search_knowledge_base("patient")
    assert len(results) > 0
    assert any(r["type"] == "fhir_resource" for r in results)
    
    # Search for diabetes scenario
    results = await search_knowledge_base("diabetes")
    assert len(results) > 0
    assert any(r["type"] == "clinical_scenario" for r in results)
    
    # Search for nothing
    results = await search_knowledge_base("xyzabc123")
    assert len(results) == 0


# ============================================================================
# RAG SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rag_service_initialization():
    """Test RAG service initialization."""
    service = RAGService()
    assert service.ollama_url
    assert service.model
    assert service.embedding_model


@pytest.mark.asyncio
async def test_retrieve_context():
    """Test context retrieval."""
    service = RAGService()
    
    # Retrieve context for Patient query
    context = await service.retrieve_context("Como criar um Patient?", top_k=3)
    assert len(context) <= 3
    assert len(context) > 0
    
    # Check context structure
    for doc in context:
        assert "type" in doc
        assert doc["type"] in ["fhir_resource", "clinical_scenario"]


@pytest.mark.asyncio
async def test_augment_prompt():
    """Test prompt augmentation."""
    service = RAGService()
    
    # Get context
    context = await service.retrieve_context("Como criar um Patient?", top_k=2)
    
    # Augment prompt
    augmented = await service.augment_prompt("Como criar um Patient?", context)
    
    assert "Contexto relevante" in augmented
    assert "Pergunta do usuário" in augmented
    assert "Como criar um Patient?" in augmented


@pytest.mark.asyncio
async def test_validate_fhir_resource():
    """Test FHIR resource validation."""
    service = RAGService()
    
    # Valid Patient
    valid_patient = {
        "resourceType": "Patient",
        "name": [{"family": "Silva", "given": ["João"]}]
    }
    result = await service.validate_fhir_resource("Patient", valid_patient)
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    
    # Invalid Patient (missing required fields)
    invalid_patient = {
        "resourceType": "Patient"
    }
    result = await service.validate_fhir_resource("Patient", invalid_patient)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("name" in error for error in result["errors"])
    
    # Wrong resource type
    wrong_type = {
        "resourceType": "Observation",
        "name": [{"family": "Silva"}]
    }
    result = await service.validate_fhir_resource("Patient", wrong_type)
    assert result["valid"] is False
    assert any("resourceType" in error for error in result["errors"])
    
    # Unknown resource type
    result = await service.validate_fhir_resource("UnknownResource", {})
    assert result["valid"] is False
    assert any("Unknown resource type" in error for error in result["errors"])


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_generate_embedding(mock_client):
    """Test embedding generation."""
    # Mock Ollama response
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_response.raise_for_status = MagicMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    service = RAGService()
    embedding = await service.generate_embedding("test text")
    
    assert len(embedding) == 3
    assert embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_generate_response_with_rag(mock_client):
    """Test response generation with RAG."""
    # Mock Ollama response
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Esta é uma resposta gerada."}
    mock_response.raise_for_status = MagicMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    service = RAGService()
    result = await service.generate_response("Como criar um Patient?", use_rag=True)
    
    assert "text" in result
    assert "sources" in result
    assert "context_used" in result
    assert result["text"] == "Esta é uma resposta gerada."
    assert result["context_used"] > 0


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_generate_response_without_rag(mock_client):
    """Test response generation without RAG."""
    # Mock Ollama response
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Resposta sem RAG."}
    mock_response.raise_for_status = MagicMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    service = RAGService()
    result = await service.generate_response("Pergunta simples", use_rag=False)
    
    assert "text" in result
    assert result["text"] == "Resposta sem RAG."
    assert result["context_used"] == 0

