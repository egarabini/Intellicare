from __future__ import annotations

from conhecimento.services import ProtocolService
from conhecimento.rag.retriever import InMemoryRetriever


class KnowledgeIndexer:
    def __init__(self, protocol_service: ProtocolService, retriever: InMemoryRetriever) -> None:
        self.protocol_service = protocol_service
        self.retriever = retriever

    def reindex_protocols(self) -> int:
        docs: list[dict] = []
        for protocol in self.protocol_service.list_protocols():
            docs.append(
                {
                    "id": f"{protocol.metadata.id}:{protocol.metadata.version}",
                    "source": "protocol",
                    "text": self._protocol_to_text(protocol),
                    "metadata": {
                        "protocol_id": protocol.metadata.id,
                        "version": protocol.metadata.version,
                        "condition": protocol.metadata.condition,
                        "specialty": protocol.metadata.specialty,
                        "status": protocol.metadata.status.value,
                    },
                }
            )
        return self.retriever.add_documents(docs)

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

