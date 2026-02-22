"""
============================================================================
NISE TRAINING MODULE - SERVICES PACKAGE
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Services Package
Versão: 1.0
Data: 25/03/2026
Responsável: DEV1
============================================================================
"""

from app.services.knowledge_base import (
    get_resource_documentation,
    get_loinc_code_info,
    get_clinical_scenario,
    search_knowledge_base,
    FHIR_KNOWLEDGE_BASE,
    CLINICAL_SCENARIOS
)

from app.services.rag_service import (
    RAGService,
    rag_service
)

__all__ = [
    # Knowledge Base
    "get_resource_documentation",
    "get_loinc_code_info",
    "get_clinical_scenario",
    "search_knowledge_base",
    "FHIR_KNOWLEDGE_BASE",
    "CLINICAL_SCENARIOS",
    
    # RAG Service
    "RAGService",
    "rag_service"
]

