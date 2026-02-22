"""SearchCache — cache Redis com TTLs diferenciados por fonte."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SearchCache:
    """
    Cache Redis para queries de busca.
    Evita cobrar Tavily para queries identicas dentro do TTL.

    Prefixos:
    - "superz:tavily:{hash}"      → TTL 6h
    - "superz:pubmed:{hash}"      → TTL 24h
    - "superz:bireme:{hash}"      → TTL 24h
    - "superz:regulatory:{hash}"  → TTL 12h

    Hash: SHA256(query + params normalizados)
    """

    TTLS: dict[str, int] = {
        "tavily": 6 * 3600,       # 6h — web muda mais rapido
        "pubmed": 24 * 3600,      # 24h — artigos nao mudam
        "bireme": 24 * 3600,
        "scielo": 24 * 3600,
        "regulatory": 12 * 3600,  # 12h — regulatorio muda menos
    }

    def __init__(self, redis_url: str = "redis://redis:6379/1", enabled: bool = True):
        self._redis_url = redis_url
        self._enabled = enabled
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Lazy-init Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                logger.warning("Redis indisponivel (%s) — cache desabilitado", e)
                self._redis = None
        return self._redis

    @staticmethod
    def _make_key(source: str, query: str, params: dict) -> str:
        """Gera chave Redis deterministica."""
        normalized = json.dumps({"q": query, **params}, sort_keys=True, ensure_ascii=False)
        h = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"superz:{source}:{h}"

    async def get(self, source: str, query: str, params: dict | None = None) -> Optional[dict]:
        """Busca no cache. Retorna None se miss ou Redis indisponivel."""
        if not self._enabled:
            return None
        try:
            r = await self._get_redis()
            if r is None:
                return None
            key = self._make_key(source, query, params or {})
            raw = await r.get(key)
            if raw:
                logger.debug("Cache HIT: %s", key)
                return json.loads(raw)
            logger.debug("Cache MISS: %s", key)
            return None
        except Exception as e:
            logger.warning("Cache get falhou: %s", e)
            return None

    async def set(self, source: str, query: str, params: dict | None = None, data: dict | None = None) -> None:
        """Salva no cache com TTL apropriado."""
        if not self._enabled or data is None:
            return
        try:
            r = await self._get_redis()
            if r is None:
                return
            key = self._make_key(source, query, params or {})
            ttl = self.TTLS.get(source, 6 * 3600)
            await r.setex(key, ttl, json.dumps(data, ensure_ascii=False))
            logger.debug("Cache SET: %s (TTL=%ds)", key, ttl)
        except Exception as e:
            logger.warning("Cache set falhou: %s", e)

    async def is_available(self) -> bool:
        """Verifica se Redis esta acessivel."""
        try:
            r = await self._get_redis()
            if r is None:
                return False
            await r.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Fecha conexao Redis."""
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None
