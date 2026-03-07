from __future__ import annotations

from fastapi.testclient import TestClient

import pytest
from conhecimento.api.app import create_app
from conhecimento.api.dependencies import get_retriever, get_indexer
from conhecimento.rag.retriever import RAGSearchResult, RAGDocument
from typing import Any

class MockRetriever:
    def query(self, text: str, top_k: int = 5, source: str | None = None) -> list[RAGSearchResult]:
        return [
            RAGSearchResult(
                document=RAGDocument(id="test", source="mock", text="mock result", metadata={}),
                score=0.9
            )
        ]

class MockIndexer:
    def reindex_protocols(self) -> int:
        return 42

@pytest.fixture(scope="module", autouse=True)
def override_dependencies():
    app = create_app()
    app.dependency_overrides[get_retriever] = lambda: MockRetriever()
    app.dependency_overrides[get_indexer] = lambda: MockIndexer()
    return app

def test_health_and_info(override_dependencies) -> None:
    client = TestClient(override_dependencies)
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/info").status_code == 200


def test_protocol_and_rag_endpoints(override_dependencies) -> None:
    client = TestClient(override_dependencies)
    protocols = client.get("/api/v1/protocolos")
    assert protocols.status_code == 200
    assert len(protocols.json()) >= 1

    reindex = client.post("/api/v1/rag/reindex")
    assert reindex.status_code == 200
    assert reindex.json()["indexed_documents"] >= 1

    query = client.post("/api/v1/rag/query", json={"query": "DRC KDIGO", "top_k": 3})
    assert query.status_code == 200
    assert len(query.json()) >= 1


def test_careplan_and_terminology_endpoints(override_dependencies) -> None:
    client = TestClient(override_dependencies)
    term = client.get("/api/v1/terminologias/cid10/N18.3")
    assert term.status_code == 200
    template = client.get("/api/v1/templates/careplan/ckd?stage=G3a")
    assert template.status_code == 200
    generated = client.post(
        "/api/v1/templates/careplan/generate",
        json={"patient_id": "p-1", "condition": "ckd", "stage": "G3a"},
    )
    assert generated.status_code == 200
    assert generated.json()["patient_id"] == "p-1"

