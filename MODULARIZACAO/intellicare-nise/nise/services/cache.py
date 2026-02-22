"""Serviço de cache Redis para NISE."""

import json
import logging
from typing import Optional, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    """Serviço de cache Redis."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300  # 5 minutos
    ):
        """
        Inicializa serviço de cache.
        
        Args:
            redis_url: URL do Redis
            default_ttl: TTL padrão em segundos
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis: Optional[redis.Redis] = None
        logger.info(f"CacheService initialized: redis_url={redis_url}, ttl={default_ttl}s")
    
    async def connect(self):
        """Conecta ao Redis."""
        if not self.redis:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
    
    async def close(self):
        """Fecha conexão Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Busca valor no cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor deserializado ou None se não encontrado
        """
        try:
            await self.connect()
            
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: key={key}")
                return json.loads(value)
            
            logger.debug(f"Cache MISS: key={key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache key={key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado (será serializado em JSON)
            ttl: TTL em segundos (usa default_ttl se None)
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            await self.connect()
            
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            
            await self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: key={key}, ttl={ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key={key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido, False caso contrário
        """
        try:
            await self.connect()
            
            result = await self.redis.delete(key)
            logger.debug(f"Cache DELETE: key={key}, deleted={result}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting cache key={key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se existe, False caso contrário
        """
        try:
            await self.connect()
            
            result = await self.redis.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error checking cache key={key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Remove todas as chaves que correspondem ao padrão.
        
        Args:
            pattern: Padrão de chave (ex: "paciente:*")
            
        Returns:
            Número de chaves removidas
        """
        try:
            await self.connect()
            
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache CLEAR: pattern={pattern}, deleted={deleted}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache pattern={pattern}: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            await self.connect()
            
            info = await self.redis.info("stats")
            return {
                "total_keys": await self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calcula taxa de acerto do cache."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

