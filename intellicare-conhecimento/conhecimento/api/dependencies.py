from __future__ import annotations

from functools import lru_cache

from conhecimento.rag.retriever import PGVectorRetriever
from conhecimento.rag.indexer import KnowledgeIndexer
from conhecimento.services import CarePlanService, ProtocolService, TerminologyService, WorkflowService


@lru_cache(maxsize=1)
def get_protocol_service() -> ProtocolService:
    return ProtocolService()


@lru_cache(maxsize=1)
def get_terminology_service() -> TerminologyService:
    return TerminologyService()


@lru_cache(maxsize=1)
def get_careplan_service() -> CarePlanService:
    return CarePlanService()


@lru_cache(maxsize=1)
def get_workflow_service() -> WorkflowService:
    return WorkflowService(get_protocol_service())


@lru_cache(maxsize=1)
def get_retriever() -> PGVectorRetriever:
    return PGVectorRetriever()


@lru_cache(maxsize=1)
def get_indexer() -> KnowledgeIndexer:
    return KnowledgeIndexer(get_protocol_service(), get_retriever())

