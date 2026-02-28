from __future__ import annotations

from ocr.storage.chroma_store import InMemoryChromaStore


def test_chroma_store_index_search_and_dedup() -> None:
    store = InMemoryChromaStore()
    first = store.index_document(
        text="Creatinina 2.1 mg/dL e potassio 5.0",
        patient_id_hash="sha256:test",
        document_type="lab_report",
        metadata={"source": "Lab A", "date": "2026-02-10"},
    )
    second = store.index_document(
        text="Creatinina 2.1 mg/dL e potassio 5.0",
        patient_id_hash="sha256:test",
        document_type="lab_report",
        metadata={"source": "Lab A", "date": "2026-02-10"},
    )
    found = store.search(
        query="creatinina",
        patient_id_hash="sha256:test",
        document_type="lab_report",
        top_k=3,
    )
    assert first["status"] == "indexed"
    assert second["status"] == "deduplicated"
    assert found["total_found"] >= 1
    assert found["patient_document_count"] == 1


def test_chroma_store_filters_by_patient() -> None:
    store = InMemoryChromaStore()
    store.index_document("A", "sha256:p1", "generic")
    store.index_document("A", "sha256:p2", "generic")
    result = store.search(query="A", patient_id_hash="sha256:p1")
    assert result["patient_document_count"] == 1

