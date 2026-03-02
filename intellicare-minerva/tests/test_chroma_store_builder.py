from __future__ import annotations

from typing import Any

import minerva.storage.chroma_store as chroma_store


def test_build_chroma_store_returns_fallback_when_chromadb_missing(monkeypatch: Any) -> None:
    fallback = chroma_store.InMemoryChromaStore()
    monkeypatch.setattr(chroma_store, "_STORE", fallback)
    monkeypatch.setattr(chroma_store, "chromadb", None)
    built = chroma_store.build_chroma_store(host="localhost", port=8200, collection="x")
    assert built is fallback


def test_build_chroma_store_returns_fallback_on_runtime_error(monkeypatch: Any) -> None:
    fallback = chroma_store.InMemoryChromaStore()
    monkeypatch.setattr(chroma_store, "_STORE", fallback)
    monkeypatch.setattr(chroma_store, "chromadb", object())

    def _raise(*_: Any, **__: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(chroma_store, "ChromaDbStore", _raise)
    built = chroma_store.build_chroma_store(host="localhost", port=8200, collection="x")
    assert built is fallback


def test_build_chroma_store_returns_chromadb_store_when_available(monkeypatch: Any) -> None:
    class FakeStore:
        pass

    monkeypatch.setattr(chroma_store, "chromadb", object())
    monkeypatch.setattr(chroma_store, "ChromaDbStore", lambda **_: FakeStore())
    built = chroma_store.build_chroma_store(host="localhost", port=8200, collection="x")
    assert isinstance(built, FakeStore)
