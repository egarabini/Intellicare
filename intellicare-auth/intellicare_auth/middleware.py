"""Middleware FastAPI para autenticação Keycloak."""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from intellicare_auth.client import KeycloakClient
from intellicare_auth.config import KeycloakConfig
from intellicare_auth.exceptions import InvalidTokenError, KeycloakConnectionError

logger = logging.getLogger(__name__)

# Security scheme para Bearer token
security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)

# Cliente Keycloak global (singleton)
_keycloak_client: Optional[KeycloakClient] = None


def get_keycloak_client() -> KeycloakClient:
    """
    Obtém instância singleton do KeycloakClient.
    
    Returns:
        KeycloakClient configurado
    """
    global _keycloak_client
    if _keycloak_client is None:
        config = KeycloakConfig()
        _keycloak_client = KeycloakClient(config)
        logger.info("KeycloakClient singleton initialized")
    return _keycloak_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    client: KeycloakClient = Depends(get_keycloak_client),
) -> Dict[str, Any]:
    """
    Dependency para obter usuário autenticado atual.
    
    Valida o token JWT e retorna o payload decodificado.
    Levanta HTTPException 401 se token inválido.
    
    Args:
        credentials: Credenciais HTTP Bearer
        client: Cliente Keycloak
        
    Returns:
        Payload do token JWT (dict com sub, preferred_username, roles, etc.)
        
    Raises:
        HTTPException: 401 se token inválido ou ausente
    
    Exemplo:
        ```python
        @app.get("/api/data")
        async def get_data(user: dict = Depends(get_current_user)):
            return {"user": user["preferred_username"]}
        ```
    """
    token = credentials.credentials
    
    try:
        user_info = await client.validate_token(token)
        logger.debug(f"User authenticated: {user_info.get('preferred_username')}")
        return user_info
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except KeycloakConnectionError as e:
        logger.error(f"Keycloak connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação temporariamente indisponível",
        )
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno de autenticação",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    client: KeycloakClient = Depends(get_keycloak_client),
) -> Optional[Dict[str, Any]]:
    """
    Dependency para obter usuário autenticado (opcional).
    
    Similar a get_current_user, mas retorna None se token ausente/inválido
    ao invés de levantar exceção.
    
    Útil para endpoints que funcionam com ou sem autenticação.
    
    Args:
        credentials: Credenciais HTTP Bearer (opcional)
        client: Cliente Keycloak
        
    Returns:
        Payload do token JWT ou None
        
    Exemplo:
        ```python
        @app.get("/api/public-data")
        async def get_public_data(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                return {"data": "personalized", "user": user["preferred_username"]}
            return {"data": "public"}
        ```
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        user_info = await client.validate_token(token)
        logger.debug(f"Optional user authenticated: {user_info.get('preferred_username')}")
        return user_info
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


def get_user_roles(user: Dict[str, Any]) -> list[str]:
    """
    Extrai roles do payload do token.
    
    Args:
        user: Payload do token JWT
        
    Returns:
        Lista de roles do usuário
        
    Exemplo:
        ```python
        user = await get_current_user()
        roles = get_user_roles(user)
        if "admin" in roles:
            # ...
        ```
    """
    # Roles podem estar em diferentes locais dependendo da configuração do Keycloak
    roles = []
    
    # Realm roles
    realm_access = user.get("realm_access", {})
    roles.extend(realm_access.get("roles", []))
    
    # Resource/client roles
    resource_access = user.get("resource_access", {})
    for client_roles in resource_access.values():
        roles.extend(client_roles.get("roles", []))
    
    return list(set(roles))  # Remove duplicatas

