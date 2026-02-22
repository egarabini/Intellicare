from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from conhecimento.rag.embeddings import EmbeddingService


@dataclass
class RAGDocument:
    id: str
    source: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float]


@dataclass
class RAGSearchResult:
    document: RAGDocument
    score: float


class InMemoryRetriever:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self._docs: list[RAGDocument] = []

    def add_documents(self, docs: list[dict[str, Any]]) -> int:
        created = 0
        for raw in docs:
            text = raw.get("text", "")
            if not text:
                continue
            doc = RAGDocument(
                id=str(raw.get("id")),
                source=str(raw.get("source", "unknown")),
                text=text,
                metadata=dict(raw.get("metadata", {})),
                embedding=self.embedding_service.embed(text),
            )
            self._docs.append(doc)
            created += 1
        return created

    def query(self, text: str, top_k: int = 5, source: str | None = None) -> list[RAGSearchResult]:
        if not text:
            return []
        query_embedding = self.embedding_service.embed(text)
        scored: list[RAGSearchResult] = []
        for doc in self._docs:
            if source and doc.source != source:
                continue
            score = self._cosine(query_embedding, doc.embedding)
            if score <= 0:
                continue
            scored.append(RAGSearchResult(document=doc, score=score))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: max(1, top_k)]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

