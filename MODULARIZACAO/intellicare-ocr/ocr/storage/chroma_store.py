"""Chroma-like in-memory store for development and tests."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import uuid4

try:
    import chromadb
except Exception:  # pragma: no cover
    chromadb = None  # type: ignore[assignment]


@dataclass(slots=True)
class IndexedDocument:
    document_id: str
    document_type: str
    patient_id_hash: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[str] = field(default_factory=list)
    content_md5: str = ""


class ChromaStoreProtocol(Protocol):
    def clear(self) -> None: ...

    def index_document(
        self,
        text: str,
        patient_id_hash: str,
        document_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def search(
        self,
        query: str,
        patient_id_hash: str,
        document_type: str = "all",
        top_k: int = 5,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]: ...


class InMemoryChromaStore:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self._chunk_size = max(64, chunk_size)
        self._chunk_overlap = max(0, min(chunk_overlap, self._chunk_size - 1))
        self._docs: dict[str, IndexedDocument] = {}
        self._by_hash: dict[str, str] = {}

    def clear(self) -> None:
        self._docs.clear()
        self._by_hash.clear()

    def index_document(
        self,
        text: str,
        patient_id_hash: str,
        document_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = text.strip()
        content_md5 = hashlib.md5(payload.encode("utf-8")).hexdigest()
        if content_md5 in self._by_hash:
            existing_id = self._by_hash[content_md5]
            existing = self._docs[existing_id]
            return {
                "document_id": existing.document_id,
                "chunks_indexed": len(existing.chunks),
                "index_time_ms": 1,
                "status": "deduplicated",
            }

        doc_id = f"doc-{uuid4()}"
        chunks = self._split_chunks(payload)
        item = IndexedDocument(
            document_id=doc_id,
            document_type=document_type,
            patient_id_hash=patient_id_hash,
            text=payload,
            metadata=metadata or {},
            chunks=chunks,
            content_md5=content_md5,
        )
        self._docs[doc_id] = item
        self._by_hash[content_md5] = doc_id
        return {
            "document_id": doc_id,
            "chunks_indexed": len(chunks),
            "index_time_ms": 5,
            "status": "indexed",
        }

    def search(
        self,
        query: str,
        patient_id_hash: str,
        document_type: str = "all",
        top_k: int = 5,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        query_terms = {token for token in query.lower().split() if token}
        results: list[dict[str, Any]] = []

        dt_from = _parse_optional_date(date_from)
        dt_to = _parse_optional_date(date_to)

        for doc in self._docs.values():
            if doc.patient_id_hash != patient_id_hash:
                continue
            if document_type != "all" and doc.document_type != document_type:
                continue

            doc_date = _parse_optional_date(str(doc.metadata.get("date"))) if doc.metadata.get("date") else None
            if dt_from and doc_date and doc_date < dt_from:
                continue
            if dt_to and doc_date and doc_date > dt_to:
                continue

            for chunk in doc.chunks:
                score = _score_chunk(query_terms, chunk)
                if score <= 0:
                    continue
                results.append(
                    {
                        "document_id": doc.document_id,
                        "document_type": doc.document_type,
                        "date": doc.metadata.get("date"),
                        "chunk": chunk,
                        "relevance_score": round(score, 4),
                        "source": doc.metadata.get("source"),
                    }
                )

        results.sort(key=lambda item: item["relevance_score"], reverse=True)
        limited = results[: max(1, min(top_k, 20))]
        return {
            "results": limited,
            "total_found": len(results),
            "patient_document_count": sum(1 for doc in self._docs.values() if doc.patient_id_hash == patient_id_hash),
        }

    def _split_chunks(self, text: str) -> list[str]:
        if not text:
            return []
        chunks: list[str] = []
        step = self._chunk_size - self._chunk_overlap
        idx = 0
        while idx < len(text):
            chunks.append(text[idx : idx + self._chunk_size])
            idx += max(1, step)
        return chunks


def _score_chunk(query_terms: set[str], chunk: str) -> float:
    if not query_terms:
        return 0.0
    chunk_lower = chunk.lower()
    matches = sum(1 for token in query_terms if token in chunk_lower)
    if matches == 0:
        return 0.0
    return matches / math.sqrt(len(query_terms))


def _parse_optional_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


_STORE: ChromaStoreProtocol = InMemoryChromaStore()


def get_chroma_store() -> ChromaStoreProtocol:
    return _STORE


def set_chroma_store(store: ChromaStoreProtocol) -> None:
    global _STORE
    _STORE = store


class ChromaDbStore:
    def __init__(self, host: str, port: int, collection: str) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb nao instalado")
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(name=collection)

    def clear(self) -> None:
        # Nao remover em producao. Em testes, chamar explicitamente se necessario.
        return

    def index_document(
        self,
        text: str,
        patient_id_hash: str,
        document_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = text.strip()
        content_md5 = hashlib.md5(payload.encode("utf-8")).hexdigest()
        document_id = f"doc-{uuid4()}"
        meta = {"patient_id_hash": patient_id_hash, "document_type": document_type, "content_md5": content_md5}
        if metadata:
            meta.update(metadata)
        self._collection.add(ids=[document_id], documents=[payload], metadatas=[meta])
        return {"document_id": document_id, "chunks_indexed": 1, "index_time_ms": 10, "status": "indexed"}

    def search(
        self,
        query: str,
        patient_id_hash: str,
        document_type: str = "all",
        top_k: int = 5,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        _ = date_from, date_to
        where: dict[str, Any] = {"patient_id_hash": patient_id_hash}
        if document_type != "all":
            where["document_type"] = document_type
        res = self._collection.query(query_texts=[query], n_results=max(1, min(top_k, 20)), where=where)
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0] if res.get("distances") else [0.0] * len(ids)
        items = []
        for idx, doc_id in enumerate(ids):
            meta = metas[idx] if idx < len(metas) and metas[idx] else {}
            distance = float(distances[idx]) if idx < len(distances) else 0.0
            items.append(
                {
                    "document_id": doc_id,
                    "document_type": meta.get("document_type"),
                    "date": meta.get("date"),
                    "chunk": docs[idx] if idx < len(docs) else "",
                    "relevance_score": round(max(0.0, 1.0 - distance), 4),
                    "source": meta.get("source"),
                }
            )
        return {"results": items, "total_found": len(items), "patient_document_count": len(items)}


def build_chroma_store(host: str, port: int, collection: str) -> ChromaStoreProtocol:
    if chromadb is None:
        return _STORE
    try:
        return ChromaDbStore(host=host, port=port, collection=collection)
    except Exception:
        return _STORE
