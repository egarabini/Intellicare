from __future__ import annotations

import hashlib
from typing import Iterable


class EmbeddingService:
    """Lightweight deterministic embedding for MVP and tests."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = max(8, dim)

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in self._tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "big") % self.dim
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = sum(value * value for value in vector) ** 0.5
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    @staticmethod
    def _tokenize(text: str) -> Iterable[str]:
        for token in (text or "").lower().split():
            clean = token.strip(".,;:!?()[]{}\"'")
            if clean:
                yield clean

