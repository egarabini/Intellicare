"""
============================================================================
NISE TRAINING MODULE - RAG SERVICE
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Retrieval-Augmented Generation Service
Versão: 1.0
Data: 25/03/2026
Responsável: DEV1
============================================================================
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import httpx
import logging
import json

from app.services.knowledge_base import (
    get_resource_documentation,
    get_loinc_code_info,
    search_knowledge_base
)

# ============================================================================
# CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://ollama:11434"
OLLAMA_MODEL = "llama2:7b"
OLLAMA_EMBEDDING_MODEL = "llama2:7b"

# ============================================================================
# RAG SERVICE
# ============================================================================

class RAGService:
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = OLLAMA_MODEL
        self.embedding_model = OLLAMA_EMBEDDING_MODEL
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ollama.
        
        Args:
            text: Text to embed
        
        Returns:
            List[float]: Embedding vector
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
    
    async def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of results to return
        
        Returns:
            List[Dict]: Relevant context documents
        """
        # Search knowledge base
        results = await search_knowledge_base(query)
        
        # Limit to top_k results
        return results[:top_k]
    
    async def augment_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        Augment user query with retrieved context.
        
        Args:
            query: User query
            context: Retrieved context documents
        
        Returns:
            str: Augmented prompt
        """
        context_text = ""
        
        for doc in context:
            if doc["type"] == "fhir_resource":
                resource_type = doc["resource_type"]
                info = doc["info"]
                context_text += f"\n\n## {resource_type}\n"
                context_text += f"{info.get('description', '')}\n"
                context_text += f"Campos obrigatórios: {', '.join(info.get('required_fields', []))}\n"
                if "example" in info:
                    context_text += f"Exemplo:\n```json\n{json.dumps(info['example'], indent=2)}\n```\n"
            
            elif doc["type"] == "clinical_scenario":
                scenario = doc["info"]
                context_text += f"\n\n## Cenário: {scenario.get('title', '')}\n"
                context_text += f"{scenario.get('description', '')}\n"
                context_text += f"Workflow:\n"
                for step in scenario.get("workflow", []):
                    context_text += f"- {step}\n"
        
        augmented_prompt = f"""Contexto relevante:
{context_text}

Pergunta do usuário: {query}

Com base no contexto acima, forneça uma resposta detalhada e educativa."""
        
        return augmented_prompt
    
    async def generate_response(
        self,
        query: str,
        system_message: Optional[str] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response using RAG.
        
        Args:
            query: User query
            system_message: Optional system message
            use_rag: Whether to use RAG (retrieve context)
        
        Returns:
            Dict: Response with text and sources
        """
        try:
            # Retrieve context if RAG is enabled
            context = []
            if use_rag:
                context = await self.retrieve_context(query)
                query = await self.augment_prompt(query, context)
            
            # Generate response using Ollama
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": query,
                        "system": system_message or "Você é Dr. Nise, um assistente de IA especializado em FHIR R4 e treinamento médico.",
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
            
            return {
                "text": result.get("response", ""),
                "sources": [doc.get("resource_type") or doc.get("scenario_id") for doc in context],
                "context_used": len(context)
            }
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "text": "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.",
                "sources": [],
                "context_used": 0,
                "error": str(e)
            }
    
    async def validate_fhir_resource(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate FHIR resource and provide suggestions.
        
        Args:
            resource_type: FHIR resource type
            resource_data: Resource data to validate
        
        Returns:
            Dict: Validation result with suggestions
        """
        doc = await get_resource_documentation(resource_type)
        
        if not doc:
            return {
                "valid": False,
                "errors": [f"Unknown resource type: {resource_type}"]
            }
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = doc.get("required_fields", [])
        for field in required_fields:
            if field not in resource_data:
                errors.append(f"Missing required field: {field}")
        
        # Check resource type
        if resource_data.get("resourceType") != resource_type:
            errors.append(f"resourceType should be '{resource_type}'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": doc.get("validation_rules", [])
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

rag_service = RAGService()

