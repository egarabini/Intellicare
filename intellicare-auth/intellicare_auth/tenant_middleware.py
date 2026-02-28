"""Middleware de tenant para FastAPI.

Fornece dependencies para injecao do TenantContext em rotas FastAPI.
Integra com o sistema de autenticacao Keycloak existente.

Cenarios suportados:
    1. tenant_id presente no JWT → fluxo normal, cria TenantContext
    2. tenants[] presente mas tenant_id ausente → HTTP 428 (precisa selecionar)
    3. Nenhum dos dois → HTTP 403 (acesso negado)

Uso:
    from intellicare_auth import get_tenant_context

    @router.get("/data")
    async def get_data(ctx: TenantContext = Depends(get_tenant_context)):
        print(ctx.tenant_id)  # "hospital_einstein"
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from intellicare_auth.middleware import get_current_user
from intellicare_core.logging.tenant_filter import bind_tenant_to_logging
from intellicare_core.tenant.context import TenantContext


async def get_tenant_context(
    request: Request,
    user: dict = Depends(get_current_user),
) -> TenantContext:
    """Dependency FastAPI que extrai TenantContext do JWT.

    Suporta 3 cenarios:
        1. tenant_id presente → cria TenantContext normalmente
        2. tenants[] presente mas tenant_id ausente → HTTP 428 (selecionar org)
        3. Nenhum dos dois → HTTP 403

    Args:
        request: Request FastAPI
        user: Payload do JWT (via get_current_user)

    Returns:
        TenantContext preenchido

    Raises:
        HTTPException: 403 se sem tenant info, 428 se tenant nao selecionado
    """
    tenant_id = user.get("tenant_id")
    tenants = user.get("tenants", [])

    # Cenario 3: nenhuma informacao de tenant
    if not tenant_id and not tenants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não contém informação de tenant. Acesso negado.",
        )

    # Cenario 2: multi-org, mas tenant nao selecionado ainda
    if not tenant_id and tenants:
        raise HTTPException(
            status_code=428,  # Precondition Required
            detail={
                "error": "tenant_not_selected",
                "message": "Selecione uma organização para continuar.",
                "available_tenants": tenants,
            },
        )

    # Cenario 1: tenant selecionado
    ctx = TenantContext.from_jwt(user)

    # Vincular tenant ao logging (structlog contextvars)
    bind_tenant_to_logging(ctx.tenant_id)

    # Armazenar no request para uso em middlewares downstream
    request.state.tenant_context = ctx

    return ctx


async def get_available_tenants(
    user: dict = Depends(get_current_user),
) -> list[str]:
    """Retorna lista de tenants disponiveis para o usuario.

    Uso na tela de selecao de organizacao (RF-F3-005).
    Este endpoint aceita tokens SEM tenant_id selecionado.

    Returns:
        Lista de tenant_ids que o usuario tem acesso
    """
    return user.get("tenants", [])


async def get_optional_tenant_context(
    request: Request,
    user: Optional[dict] = Depends(get_current_user),
) -> Optional[TenantContext]:
    """Para endpoints que funcionam com ou sem tenant.

    Usado em endpoints de plataforma que opcionalmente filtram por tenant.
    Nao levanta excecao se tenant nao estiver presente.

    Returns:
        TenantContext se disponivel, None caso contrario
    """
    if not user:
        return None

    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return None

    ctx = TenantContext.from_jwt(user)
    bind_tenant_to_logging(ctx.tenant_id)
    request.state.tenant_context = ctx
    return ctx
