"""Middleware FastAPI de resolução multi-fonte de tenant.

Evolução do tenant_middleware.py original (apenas JWT) para suportar
múltiplas fontes de resolução: JWT, Header, Subdomínio, Path.

Mantém backward compatibility total — os mesmos Depends() funcionam,
mas agora suportam resolução via subdomínio quando não há JWT.

Uso:
    from intellicare_auth.tenant_resolver_middleware import (
        get_tenant_context,
        get_optional_tenant_context,
        create_tenant_resolver,
    )

    # No app.py do módulo:
    resolver = create_tenant_resolver()

    @router.get("/data")
    async def get_data(ctx: TenantContext = Depends(get_tenant_context)):
        print(ctx.tenant_id)  # Resolvido via JWT ou subdomínio
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from intellicare_core.logging.tenant_filter import bind_tenant_to_logging
from intellicare_core.tenant.context import TenantContext
from intellicare_core.tenant.resolver import TenantResolver, ResolvedTenant

import structlog

logger = structlog.get_logger(__name__)

# ── Instância global do resolver (configurável via create_tenant_resolver) ──
_resolver: Optional[TenantResolver] = None


def create_tenant_resolver(
    platform_domains: Optional[list[str]] = None,
    module_domains: Optional[list[str]] = None,
    enable_path_resolution: bool = False,
    enable_query_resolution: bool = False,
) -> TenantResolver:
    """Cria e registra o TenantResolver global.

    Chamar uma vez no startup do módulo (app.py).

    Args:
        platform_domains: Domínios da plataforma (default: ["intellicare.ia.br"])
        module_domains: Domínios dos módulos (default: ["saudeconectada.com.br"])
        enable_path_resolution: Habilitar resolução por URL path
        enable_query_resolution: Habilitar resolução por query param (dev only)

    Returns:
        TenantResolver configurado
    """
    global _resolver
    _resolver = TenantResolver(
        platform_domains=platform_domains or ["intellicare.ia.br"],
        module_domains=module_domains or ["saudeconectada.com.br"],
        enable_path_resolution=enable_path_resolution,
        enable_query_resolution=enable_query_resolution,
    )
    logger.info(
        "tenant_resolver.configured",
        platform_domains=_resolver.platform_domains,
        module_domains=_resolver.module_domains,
    )
    return _resolver


def _get_resolver() -> TenantResolver:
    """Retorna o resolver global, criando um default se necessário."""
    global _resolver
    if _resolver is None:
        _resolver = TenantResolver()
    return _resolver


def _try_get_user(request: Request) -> Optional[dict]:
    """Tenta obter o usuário do JWT sem falhar.

    Permite resolução de tenant mesmo sem autenticação
    (ex: via subdomínio antes do login).
    """
    try:
        from intellicare_auth.middleware import get_current_user
        # get_current_user é um Depends, mas podemos chamar diretamente
        # se o request já tem o user setado pelo auth middleware
        user = getattr(request.state, "user", None)
        return user
    except (ImportError, AttributeError):
        return None


async def get_tenant_context(
    request: Request,
) -> TenantContext:
    """Dependency FastAPI que resolve TenantContext multi-fonte.

    Ordem de resolução:
        1. JWT claim (tenant_id) — se usuário autenticado
        2. Header X-Tenant-ID — injetado pelo Traefik/gateway
        3. Subdomínio — {tenant}.saudeconectada.com.br
        4. Path / Query param — se habilitado

    Cenários de erro:
        - Nenhuma fonte → HTTP 403
        - Multi-org sem seleção → HTTP 428

    Falls back to original JWT-only behavior when no resolver configured.
    """
    resolver = _get_resolver()

    # Obter JWT payload se disponível
    jwt_payload = getattr(request.state, "user", None)

    # Resolver tenant
    resolved = resolver.resolve(request, jwt_payload=jwt_payload)

    # Se resolvido, criar TenantContext
    if resolved.is_resolved:
        ctx = _create_context(resolved, jwt_payload)
        bind_tenant_to_logging(ctx.tenant_id)
        request.state.tenant_context = ctx
        request.state.tenant_resolved = resolved
        return ctx

    # Se JWT tem tenants[] mas não tenant_id → multi-org, precisa selecionar
    if jwt_payload:
        tenants = jwt_payload.get("tenants", [])
        if tenants:
            raise HTTPException(
                status_code=428,  # Precondition Required
                detail={
                    "error": "tenant_not_selected",
                    "message": "Selecione uma organização para continuar.",
                    "available_tenants": tenants,
                },
            )

    # Nenhuma fonte de tenant
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Não foi possível determinar o tenant. Acesso negado.",
    )


async def get_optional_tenant_context(
    request: Request,
) -> Optional[TenantContext]:
    """Para endpoints que funcionam com ou sem tenant.

    Nunca levanta exceção — retorna None se não conseguir resolver.
    """
    resolver = _get_resolver()
    jwt_payload = getattr(request.state, "user", None)
    resolved = resolver.resolve(request, jwt_payload=jwt_payload)

    if resolved.is_resolved:
        ctx = _create_context(resolved, jwt_payload)
        bind_tenant_to_logging(ctx.tenant_id)
        request.state.tenant_context = ctx
        request.state.tenant_resolved = resolved
        return ctx

    return None


async def get_tenant_from_subdomain(
    request: Request,
) -> Optional[str]:
    """Resolve tenant_id APENAS pelo subdomínio (sem JWT).

    Usado antes da autenticação (ex: tela de login white-label,
    branding por domínio, redirecionamento para Keycloak tenant-specific).
    """
    resolver = _get_resolver()
    resolved = resolver._from_subdomain(request)
    return resolved.tenant_id if resolved.is_resolved else None


async def get_available_tenants(
    request: Request,
) -> list[str]:
    """Retorna lista de tenants disponíveis para o usuário.

    Combina tenants do JWT com o tenant resolvido por outras fontes.
    """
    jwt_payload = getattr(request.state, "user", None)
    tenants = []

    if jwt_payload:
        tenants = jwt_payload.get("tenants", [])

    # Se tenant resolvido por subdomain e não está na lista, adicionar
    resolver = _get_resolver()
    resolved = resolver._from_subdomain(request)
    if resolved.is_resolved and resolved.tenant_id not in tenants:
        tenants.append(resolved.tenant_id)

    return tenants


def _create_context(
    resolved: ResolvedTenant,
    jwt_payload: Optional[dict] = None,
) -> TenantContext:
    """Cria TenantContext a partir do resultado da resolução.

    Se o tenant veio do JWT, usa from_jwt() para pegar roles etc.
    Se veio de outra fonte, cria manualmente com dados limitados.
    """
    if resolved.source == "jwt" and jwt_payload:
        return TenantContext.from_jwt(jwt_payload)

    # Tenant resolvido por fonte não-JWT (subdomain, header, path)
    tenant_id = resolved.tenant_id

    # Se temos JWT mas o tenant veio de outra fonte, pegar user info do JWT
    user_id = ""
    user_roles = []
    available_tenants = []

    if jwt_payload:
        user_id = jwt_payload.get("sub", "")
        user_roles = TenantContext._extract_roles(jwt_payload)
        available_tenants = jwt_payload.get("tenants", [])

    return TenantContext(
        tenant_id=tenant_id,
        tenant_schema=f"tenant_{tenant_id}",
        user_id=user_id,
        user_roles=user_roles,
        available_tenants=available_tenants,
    )
