"""IntelliCare Tenant — Infraestrutura de multi-tenancy.

Este pacote fornece os componentes necessarios para isolamento
de dados e contexto entre tenants (organizacoes/hospitais).

Componentes:
    - TenantContext: Contexto imutavel do tenant por requisicao
    - TenantAwareSessionFactory: Factory de sessions com schema isolation
    - TenantRedisClient: Redis client com prefixo de tenant automatico
"""

from intellicare_core.tenant.context import TenantContext
from intellicare_core.tenant.session import TenantAwareSessionFactory
from intellicare_core.tenant.redis import TenantRedisClient

__all__ = [
    "TenantContext",
    "TenantAwareSessionFactory",
    "TenantRedisClient",
]
