"""RAG (Retrieval-Augmented Generation) para protocolos clínicos."""

from florence.engine.rag.indexer import ProtocolIndexer
from florence.engine.rag.retriever import ProtocolRetriever
from florence.engine.rag.models import Protocol, RAGQuery, RAGResult

__all__ = [
    "ProtocolIndexer",
    "ProtocolRetriever",
    "Protocol",
    "RAGQuery",
    "RAGResult",
]

