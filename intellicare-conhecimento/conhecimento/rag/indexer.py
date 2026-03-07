from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from langchain_huggingface import HuggingFaceEmbeddings

from conhecimento.services import ProtocolService
from conhecimento.rag.retriever import PGVectorRetriever
from conhecimento.models.document import Document
from conhecimento.storage.db import engine

class KnowledgeIndexer:
    def __init__(self, protocol_service: ProtocolService, retriever: PGVectorRetriever) -> None:
        self.protocol_service = protocol_service
        self.retriever = retriever
        self.embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

    def reindex_protocols(self) -> int:
        count = 0
        with Session(engine) as session:
            # First, clean existing protocol documents if needed
            # session.query(Document).filter(Document.source == "protocol").delete()
            
            for protocol in self.protocol_service.list_protocols():
                protocol_id = f"{protocol.metadata.id}:{protocol.metadata.version}"
                
                # Check if it already exists
                existing = session.query(Document).filter(Document.id == protocol_id).first()
                if existing:
                    continue
                
                text = self._protocol_to_text(protocol)
                vector = self.embeddings.embed_query(text)
                
                doc = Document(
                    id=protocol_id,
                    source="protocol",
                    content=text,
                    metadata_={
                        "protocol_id": protocol.metadata.id,
                        "version": protocol.metadata.version,
                        "condition": protocol.metadata.condition,
                        "specialty": protocol.metadata.specialty,
                        "status": protocol.metadata.status.value,
                    },
                    embedding=vector
                )
                session.add(doc)
                count += 1
            session.commit()
        return count

    @staticmethod
    def _protocol_to_text(protocol) -> str:
        sections = "\n".join(f"{section.title}: {section.content}" for section in protocol.sections)
        return (
            f"{protocol.metadata.title}\n"
            f"{protocol.summary}\n"
            f"Condition: {protocol.metadata.condition}\n"
            f"Specialty: {protocol.metadata.specialty}\n"
            f"Keywords: {' '.join(protocol.metadata.keywords)}\n"
            f"Sections:\n{sections}"
        )

