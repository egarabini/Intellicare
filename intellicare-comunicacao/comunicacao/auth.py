"""Middleware de autenticação e autorização para o módulo de comunicação."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Flag para indicar se intellicare-auth está disponível
_AUTH_AVAILABLE = False
_keycloak_client = None

try:
    from intellicare_auth import (
        KeycloakClient,
        KeycloakConfig,
        get_current_user as _get_current_user,
        get_optional_user as _get_optional_user,
        get_user_roles as _get_user_roles,
        requires_any_role as _requires_any_role,
        get_tenant_context as _get_tenant_context,
    )
    _AUTH_AVAILABLE = True
    logger.info("intellicare-auth disponível - autenticação habilitada")
except ImportError:
    logger.warning(
        "intellicare-auth não disponível - autenticação desabilitada. "
        "Instale com: pip install -e ../intellicare-auth"
    )


# Security scheme para Bearer token (must be after _AUTH_AVAILABLE is set)
security = HTTPBearer(auto_error=_AUTH_AVAILABLE)
optional_security = HTTPBearer(auto_error=False)


def init_keycloak_client() -> None:
    """Inicializa o cliente Keycloak global."""
    global _keycloak_client
    if _AUTH_AVAILABLE and _keycloak_client is None:
        try:
            config = KeycloakConfig()
            _keycloak_client = KeycloakClient(config)
            logger.info("KeycloakClient inicializado com sucesso")
        except Exception as exc:
            logger.error("Falha ao inicializar KeycloakClient: %s", exc)
            raise


def get_keycloak_client() -> Any:
    """Retorna o cliente Keycloak global."""
    if not _AUTH_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação não disponível - intellicare-auth não instalado",
        )
    if _keycloak_client is None:
        init_keycloak_client()
    return _keycloak_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """
    Dependency para obter usuário autenticado atual.
    
    Se intellicare-auth não estiver disponível, retorna um usuário mock para desenvolvimento.
    
    Args:
        credentials: Credenciais HTTP Bearer
        
    Returns:
        Payload do token JWT (dict com sub, preferred_username, roles, etc.)
        
    Raises:
        HTTPException: 401 se token inválido ou ausente
    """
    if not _AUTH_AVAILABLE:
        # Modo desenvolvimento - retorna usuário mock
        logger.warning("Autenticação desabilitada - retornando usuário mock")
        return {
            "sub": "dev-user-123",
            "preferred_username": "dev_user",
            "email": "dev@intellicare.health",
            "realm_access": {
                "roles": ["intellicare_admin", "intellicare_user", "comunicacao_admin"]
            },
        }
    
    # Modo produção - valida token via Keycloak
    return await _get_current_user(credentials, get_keycloak_client())


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> dict[str, Any] | None:
    """
    Dependency para obter usuário autenticado opcional.
    
    Retorna None se não houver token.
    
    Args:
        credentials: Credenciais HTTP Bearer (opcional)
        
    Returns:
        Payload do token JWT ou None
    """
    if credentials is None:
        return None
    
    if not _AUTH_AVAILABLE:
        # Modo desenvolvimento - retorna usuário mock
        return {
            "sub": "dev-user-123",
            "preferred_username": "dev_user",
            "email": "dev@intellicare.health",
            "realm_access": {
                "roles": ["intellicare_admin", "intellicare_user", "comunicacao_admin"]
            },
        }
    
    # Modo produção - valida token via Keycloak
    return await _get_optional_user(credentials, get_keycloak_client())


def get_user_roles(user: dict[str, Any]) -> list[str]:
    """
    Extrai roles do payload do token.

    Args:
        user: Payload do token JWT

    Returns:
        Lista de roles do usuário
    """
    if not _AUTH_AVAILABLE:
        # Modo desenvolvimento - retorna roles do mock
        realm_access = user.get("realm_access", {})
        return realm_access.get("roles", [])

    return _get_user_roles(user)


def requires_role(role: str):
    """
    Decorator que exige uma role específica.

    Se intellicare-auth não estiver disponível, permite acesso (modo desenvolvimento).

    Args:
        role: Role requerida

    Returns:
        Decorator function

    Raises:
        HTTPException: 403 se usuário não tem a role

    Exemplo:
        ```python
        @app.post("/api/v1/routing/send")
        @requires_role("comunicacao_send")
        async def send_intent(user: dict = Depends(get_current_user)):
            return {"message": "Intent sent"}
        ```
    """
    if not _AUTH_AVAILABLE:
        # Modo desenvolvimento - decorator vazio
        def decorator(func):
            return func
        return decorator

    return _requires_role(role)


def requires_any_role(roles: list[str]):
    """
    Decorator que exige pelo menos uma das roles especificadas.

    Se intellicare-auth não estiver disponível, permite acesso (modo desenvolvimento).

    Args:
        roles: Lista de roles (usuário precisa ter pelo menos uma)

    Returns:
        Decorator function

    Raises:
        HTTPException: 403 se usuário não tem nenhuma das roles

    Exemplo:
        ```python
        @app.get("/api/v1/routing/intents")
        @requires_any_role(["comunicacao_read", "comunicacao_admin"])
        async def list_intents(user: dict = Depends(get_current_user)):
            return {"intents": [...]}
        ```
    """
    if not _AUTH_AVAILABLE:
        # Modo desenvolvimento - decorator vazio
        def decorator(func):
            return func
        return decorator

    return _requires_any_role(roles)


async def get_tenant_context(request: Request) -> Any:
    """
    Dependency para obter o contexto do tenant atual (Multi-Tenant).
    
    Se intellicare-auth não estiver disponível, retorna o TenantContext default (desenvolvimento).
    """
    if not _AUTH_AVAILABLE:
        from intellicare_core.tenant import TenantContext
        return TenantContext.default()
    
    return await _get_tenant_context(request)


def check_module_active(module_name: str):
    """
    Retorna uma Dependency do FastAPI que verifica se o módulo está ativo para o tenant.
    """
    async def _check(ctx: Any = Depends(get_tenant_context)):
        if not _AUTH_AVAILABLE or ctx.tenant_id == "default":
            return
            
        import os
        from intellicare_core.tenant.redis import TenantRedisClient
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        try:
            client = TenantRedisClient(redis_url)
            # A chave de cache no Redis já herda o prefixo "tenant:{id}:"
            cached = await client.get(ctx, f"modules:{module_name}:active")
            
            if cached is not None and cached in ("0", b"0", "false", b"false", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail=f"Módulo '{module_name}' não disponível para esta organização"
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Falha ao validar module %s active redis cache: %s", module_name, exc)
            pass # Fail open if redis is down for active checks unless strict config is present
    
    return Depends(_check)

