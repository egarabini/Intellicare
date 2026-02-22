"""Redis client com isolamento automatico por tenant.

Todas as operacoes de cache Redis sao automaticamente prefixadas
com o identificador do tenant, garantindo isolamento de dados
entre organizacoes diferentes.

Formato da key: tenant:{tenant_id}:{key}
Exemplo: tenant:hospital_einstein:zilda:cnes:2077485

Uso:
    redis = TenantRedisClient(redis_url)
    await redis.set(ctx, "zilda:cnes:2077485", data, ttl=3600)
    result = await redis.get(ctx, "zilda:cnes:2077485")
    # Key real no Redis: tenant:hospital_einstein:zilda:cnes:2077485
"""

from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from intellicare_core.tenant.context import TenantContext


class TenantRedisClient:
    """Redis client com prefixo de tenant automatico.

    Cada operacao de leitura/escrita e automaticamente prefixada
    com tenant:{tenant_id}: para garantir isolamento.
    """

    def __init__(self, redis_url: str, key_prefix: str = "") -> None:
        """Inicializa o client Redis.

        Args:
            redis_url: URL de conexao Redis
            key_prefix: Prefixo adicional opcional (ex: nome do modulo)
        """
        self._redis = aioredis.from_url(
            redis_url,
            decode_responses=True,
        )
        self._key_prefix = key_prefix

    def _key(self, ctx: TenantContext, key: str) -> str:
        """Gera a key Redis com prefixo do tenant.

        Args:
            ctx: Contexto do tenant
            key: Key original

        Returns:
            Key prefixada: tenant:{tenant_id}:{prefix}:{key}
        """
        parts = ["tenant", ctx.tenant_id]
        if self._key_prefix:
            parts.append(self._key_prefix)
        parts.append(key)
        return ":".join(parts)

    # ─── Operacoes basicas ───────────────────────────────────

    async def get(self, ctx: TenantContext, key: str) -> Optional[str]:
        """Busca um valor do cache isolado por tenant."""
        return await self._redis.get(self._key(ctx, key))

    async def set(
        self,
        ctx: TenantContext,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> None:
        """Armazena um valor no cache isolado por tenant.

        Args:
            ctx: Contexto do tenant
            key: Chave do cache
            value: Valor a armazenar (string)
            ttl: Time-to-live em segundos (None = sem expiracao)
        """
        await self._redis.set(self._key(ctx, key), value, ex=ttl)

    async def delete(self, ctx: TenantContext, key: str) -> int:
        """Remove uma key do cache do tenant.

        Returns:
            Numero de keys removidas (0 ou 1)
        """
        return await self._redis.delete(self._key(ctx, key))

    async def exists(self, ctx: TenantContext, key: str) -> bool:
        """Verifica se uma key existe no cache do tenant."""
        return bool(await self._redis.exists(self._key(ctx, key)))

    # ─── Operacoes JSON ──────────────────────────────────────

    async def get_json(self, ctx: TenantContext, key: str) -> Optional[Any]:
        """Busca e deserializa um valor JSON do cache."""
        raw = await self.get(ctx, key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(
        self,
        ctx: TenantContext,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Serializa e armazena um valor JSON no cache."""
        await self.set(ctx, key, json.dumps(value, default=str), ttl=ttl)

    # ─── Operacoes de contagem ───────────────────────────────

    async def incr(self, ctx: TenantContext, key: str) -> int:
        """Incrementa um contador no cache do tenant."""
        return await self._redis.incr(self._key(ctx, key))

    async def decr(self, ctx: TenantContext, key: str) -> int:
        """Decrementa um contador no cache do tenant."""
        return await self._redis.decr(self._key(ctx, key))

    # ─── Pub/Sub ─────────────────────────────────────────────

    async def publish(self, ctx: TenantContext, channel: str, message: str) -> int:
        """Publica uma mensagem em um canal isolado por tenant.

        Args:
            ctx: Contexto do tenant
            channel: Nome do canal (sera prefixado com tenant)
            message: Mensagem a publicar

        Returns:
            Numero de assinantes que receberam a mensagem
        """
        return await self._redis.publish(self._key(ctx, channel), message)

    # ─── Administrativo ──────────────────────────────────────

    async def flush_tenant(self, ctx: TenantContext) -> int:
        """Remove TODAS as keys de um tenant especifico.

        ⚠ CUIDADO: Operacao destrutiva. Usar apenas em testes ou deprovisionamento.

        Returns:
            Numero de keys removidas
        """
        pattern = f"tenant:{ctx.tenant_id}:*"
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self._redis.delete(*keys)
        return 0

    async def close(self) -> None:
        """Fecha a conexao Redis."""
        await self._redis.close()

    @property
    def redis(self) -> aioredis.Redis:
        """Acesso direto ao client Redis (para operacoes avancadas)."""
        return self._redis
