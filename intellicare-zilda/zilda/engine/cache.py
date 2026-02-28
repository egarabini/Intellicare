"""Cache simples com TTL para dados do CNES."""

import time
from typing import Any


class SimpleCache:
    """Cache in-memory com TTL por chave."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        """Retorna valor se existir e nao expirado."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Armazena valor com TTL em segundos."""
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        """Remove uma chave."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Limpa todo o cache."""
        self._store.clear()

    def has(self, key: str) -> bool:
        """Verifica se chave existe e nao expirou."""
        return self.get(key) is not None

    def size(self) -> int:
        """Retorna numero de entradas (inclui expiradas)."""
        return len(self._store)

    def cleanup(self) -> int:
        """Remove entradas expiradas. Retorna numero de removidas."""
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)
