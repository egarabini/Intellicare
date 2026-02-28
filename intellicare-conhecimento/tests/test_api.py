from __future__ import annotations

from fastapi.testclient import TestClient

from conhecimento.api.app import create_app


def test_health_and_info() -> None:
    client = TestClient(create_app())
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/info").status_code == 200


def test_protocol_and_rag_endpoints() -> None:
    client = TestClient(create_app())
    protocols = client.get("/api/v1/protocolos")
    assert protocols.status_code == 200
    assert len(protocols.json()) >= 1

    reindex = client.post("/api/v1/rag/reindex")
    assert reindex.status_code == 200
    assert reindex.json()["indexed_documents"] >= 1

    query = client.post("/api/v1/rag/query", json={"query": "DRC KDIGO", "top_k": 3})
    assert query.status_code == 200
    assert len(query.json()) >= 1


def test_careplan_and_terminology_endpoints() -> None:
    client = TestClient(create_app())
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

