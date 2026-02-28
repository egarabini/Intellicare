"""Helper para inicializar o TenantResolver no startup de módulos FastAPI.

Centraliza a configuração do TenantResolver para ser chamado
no lifespan de cada módulo.

Uso (no app.py do módulo):
    from intellicare_core.tenant.startup import init_tenant_resolver

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_tenant_resolver()   # ← adicionar no início
        ...
        yield

Ou via intellicare-auth:
    from intellicare_auth.tenant_resolver_middleware import create_tenant_resolver

    create_tenant_resolver()  # Cria instância global
"""

from __future__ import annotations

import os

import structlog

from intellicare_core.tenant.resolver import TenantResolver

logger = structlog.get_logger(__name__)

# Domínios configuráveis via env
_DEFAULT_PLATFORM_DOMAINS = ["intellicare.ia.br"]
_DEFAULT_MODULE_DOMAINS = ["saudeconectada.com.br"]


def init_tenant_resolver() -> TenantResolver:
    """Inicializa o TenantResolver global com config do ambiente.

    Environment variables:
        TENANT_PLATFORM_DOMAINS: Domínios da plataforma (CSV)
        TENANT_MODULE_DOMAINS: Domínios dos módulos (CSV)
        TENANT_ENABLE_PATH: Habilitar resolução por path (true/false)
        TENANT_ENABLE_QUERY: Habilitar resolução por query (dev only)

    Returns:
        TenantResolver configurado e registrado globalmente
    """
    platform_domains = _parse_csv(
        os.getenv("TENANT_PLATFORM_DOMAINS", ""),
        default=_DEFAULT_PLATFORM_DOMAINS,
    )
    module_domains = _parse_csv(
        os.getenv("TENANT_MODULE_DOMAINS", ""),
        default=_DEFAULT_MODULE_DOMAINS,
    )
    enable_path = os.getenv("TENANT_ENABLE_PATH", "false").lower() == "true"
    enable_query = os.getenv("TENANT_ENABLE_QUERY", "false").lower() == "true"

    resolver = TenantResolver(
        platform_domains=platform_domains,
        module_domains=module_domains,
        enable_path_resolution=enable_path,
        enable_query_resolution=enable_query,
    )

    # Registrar no módulo de auth também (se disponível)
    try:
        from intellicare_auth.tenant_resolver_middleware import _resolver
        import intellicare_auth.tenant_resolver_middleware as trm
        trm._resolver = resolver
    except ImportError:
        pass

    logger.info(
        "tenant_resolver.initialized",
        platform_domains=platform_domains,
        module_domains=module_domains,
        path_resolution=enable_path,
        query_resolution=enable_query,
    )

    return resolver


def _parse_csv(value: str, default: list[str]) -> list[str]:
    """Parse comma-separated string to list, with default fallback."""
    if not value.strip():
        return default
    return [d.strip() for d in value.split(",") if d.strip()]
