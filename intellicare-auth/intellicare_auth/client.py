"""Cliente Keycloak para validação de tokens e autenticação."""

import logging
from typing import Any, Dict, Optional

import httpx
import jwt
from cachetools import TTLCache
from jwt import PyJWKClient

from intellicare_auth.config import KeycloakConfig
from intellicare_auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    KeycloakConnectionError,
)

logger = logging.getLogger(__name__)


class KeycloakClient:
    """
    Cliente para integração com Keycloak GSI.
    
    Fornece:
    - Validação de tokens JWT (local com JWKS)
    - Obtenção de tokens (client credentials)
    - Cache de JWKS e tokens validados
    - Retry automático em caso de falha
    """

    def __init__(self, config: Optional[KeycloakConfig] = None):
        """
        Inicializa o cliente Keycloak.
        
        Args:
            config: Configuração do Keycloak. Se None, carrega de variáveis de ambiente.
        """
        self.config = config or KeycloakConfig()
        
        # Cache JWKS (JSON Web Key Set)
        self._jwks_cache: TTLCache = TTLCache(
            maxsize=1,
            ttl=self.config.jwks_cache_ttl
        )
        
        # Cache de tokens validados
        self._token_cache: TTLCache = TTLCache(
            maxsize=1000,
            ttl=self.config.token_cache_ttl
        )
        
        # Cliente JWKS para validação de assinaturas
        self._jwks_client: Optional[PyJWKClient] = None
        
        logger.info(
            f"KeycloakClient initialized for realm '{self.config.realm}' "
            f"at '{self.config.server_url}'"
        )

    def _get_jwks_client(self) -> PyJWKClient:
        """Obtém ou cria cliente JWKS."""
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(
                self.config.jwks_uri,
                cache_keys=True,
                max_cached_keys=10,
                cache_jwk_set=True,
                lifespan=self.config.jwks_cache_ttl,
            )
        return self._jwks_client

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valida token JWT localmente usando JWKS.
        
        Args:
            token: Token JWT (access_token)
            
        Returns:
            Payload decodificado do token
            
        Raises:
            InvalidTokenError: Token inválido ou expirado
            KeycloakConnectionError: Erro ao buscar JWKS
        """
        # Verificar cache
        cached = self._token_cache.get(token)
        if cached:
            logger.debug("Token found in cache")
            return cached

        try:
            # Obter chave pública do JWKS
            jwks_client = self._get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Decodificar e validar token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.config.client_id if self.config.validate_audience else None,
                issuer=self.config.issuer if self.config.validate_issuer else None,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": self.config.validate_audience,
                    "verify_iss": self.config.validate_issuer,
                }
            )
            
            # Armazenar em cache
            self._token_cache[token] = payload
            
            logger.debug(f"Token validated successfully for user: {payload.get('preferred_username')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise InvalidTokenError("Token expirado")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise InvalidTokenError(f"Token inválido: {str(e)}")
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise KeycloakConnectionError(f"Erro ao validar token: {str(e)}")

    async def get_client_token(self) -> Dict[str, Any]:
        """
        Obtém token usando client credentials flow.
        
        Returns:
            Dict com access_token, token_type, expires_in, etc.
            
        Raises:
            AuthenticationError: Falha na autenticação
            KeycloakConnectionError: Erro de conexão
        """
        if not self.config.client_secret:
            raise AuthenticationError("Client secret não configurado")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.read_timeout,
                ),
                verify=self.config.verify_ssl,
            ) as client:
                response = await client.post(
                    self.config.token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get token: {response.status_code} - {response.text}")
                    raise AuthenticationError(f"Falha ao obter token: {response.status_code}")
                
                token_data = response.json()
                logger.info("Client token obtained successfully")
                return token_data
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting token: {e}")
            raise KeycloakConnectionError(f"Erro de conexão: {str(e)}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Obtém informações do usuário via endpoint /userinfo.

        Args:
            token: Access token

        Returns:
            Informações do usuário

        Raises:
            KeycloakConnectionError: Erro de conexão
        """
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.read_timeout,
                ),
                verify=self.config.verify_ssl,
            ) as client:
                response = await client.get(
                    self.config.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code != 200:
                    logger.error(f"Failed to get user info: {response.status_code}")
                    raise KeycloakConnectionError(f"Erro ao obter user info: {response.status_code}")

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting user info: {e}")
            raise KeycloakConnectionError(f"Erro de conexão: {str(e)}")

    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Introspecta token via endpoint /introspect (fallback se validação local falhar).

        Args:
            token: Access token

        Returns:
            Informações do token (active, exp, iat, etc.)

        Raises:
            AuthenticationError: Client secret não configurado
            KeycloakConnectionError: Erro de conexão
        """
        if not self.config.client_secret:
            raise AuthenticationError("Client secret necessário para introspecção")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.read_timeout,
                ),
                verify=self.config.verify_ssl,
            ) as client:
                response = await client.post(
                    self.config.introspection_endpoint,
                    data={
                        "token": token,
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(f"Failed to introspect token: {response.status_code}")
                    raise KeycloakConnectionError(f"Erro ao introspectar token: {response.status_code}")

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error introspecting token: {e}")
            raise KeycloakConnectionError(f"Erro de conexão: {str(e)}")

    def clear_caches(self) -> None:
        """Limpa todos os caches (útil para testes ou troubleshooting)."""
        self._jwks_cache.clear()
        self._token_cache.clear()
        logger.info("All caches cleared")

