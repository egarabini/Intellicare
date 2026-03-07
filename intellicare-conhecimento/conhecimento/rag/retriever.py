from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import Session
from langchain_huggingface import HuggingFaceEmbeddings

from conhecimento.models.document import Document
from conhecimento.storage.db import engine

@dataclass
class RAGDocument:
    id: str
    source: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float] = None

@dataclass
class RAGSearchResult:
    document: RAGDocument
    score: float

class PGVectorRetriever:
    """Retriever that queries the PostgreSQL Database using pgvector L2 distance."""
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small") -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

    def query(self, text: str, top_k: int = 5, source: str | None = None) -> list[RAGSearchResult]:
        if not text:
            return []
            
        # 1. Genereate query embedding
        query_vector = self.embeddings.embed_query(text)
        
        # 2. Query Postgres
        scored_results = []
        with Session(engine) as session:
            # We order by pgvector's L2 distance: Vector.l2_distance(query_vector)
            # The smaller the distance, the more similar the texts.
            # So, relevance score can be conceptualized as 1 / (1 + distance) 
            stmt = session.query(Document)
            if source:
                stmt = stmt.filter(Document.source == source)
                
            docs = stmt.order_by(Document.embedding.l2_distance(query_vector)).limit(top_k).all()
            
            for doc in docs:
                distance = doc.embedding.l2_distance(query_vector) if doc.embedding else 1.0
                # Assuming l2_distance is evaluated directly in DB, 
                # but SQLAlchemy requires .scalar() or similar if querying just the distance.
                # To get both doc and distance efficiently:
                pass
                
        # Better approach: request doc and distance together
        with Session(engine) as session:
            stmt = session.query(Document, Document.embedding.l2_distance(query_vector).label('distance'))
            if source:
                stmt = stmt.filter(Document.source == source)
                
            results = stmt.order_by('distance').limit(top_k).all()
            
            for doc, distance in results:
                rag_doc = RAGDocument(
                    id=doc.id,
                    source=doc.source,
                    text=doc.content,
                    metadata=doc.metadata_
                )
                # Convert distance to a similarity score (0 to 1)
                score = 1.0 / (1.0 + float(distance))
                scored_results.append(RAGSearchResult(document=rag_doc, score=score))
                
        return scored_results
