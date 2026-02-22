"""Cliente para Keycloak Admin API."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from comunicacao.sync.models import KeycloakUser

logger = logging.getLogger(__name__)


class KeycloakConfig(BaseModel):
    """Configuração do Keycloak Admin API."""
    
    url: str = Field(..., description="URL do Keycloak (ex: https://keycloak.gsi.srv.br)")
    admin_realm: str = Field("master", description="Realm do admin")
    admin_username: str = Field(..., description="Username do admin")
    admin_password: str = Field(..., description="Senha do admin")
    target_realm: str = Field("bemcuidar", description="Realm alvo")
    
    @classmethod
    def from_env(cls) -> KeycloakConfig:
        """Cria configuração a partir de variáveis de ambiente."""
        import os
        
        return cls(
            url=os.getenv("KEYCLOAK_ADMIN_URL", "https://keycloak.gsi.srv.br"),
            admin_realm=os.getenv("KEYCLOAK_ADMIN_REALM", "master"),
            admin_username=os.getenv("KEYCLOAK_ADMIN_USERNAME", ""),
            admin_password=os.getenv("KEYCLOAK_ADMIN_PASSWORD", ""),
            target_realm=os.getenv("KEYCLOAK_TARGET_REALM", "bemcuidar"),
        )


class KeycloakAdminClient:
    """Cliente para Keycloak Admin API."""
    
    def __init__(self, config: KeycloakConfig | None = None):
        """
        Inicializa cliente.
        
        Args:
            config: Configuração do Keycloak (se None, usa from_env())
        """
        if config is None:
            config = KeycloakConfig.from_env()
        
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._access_token: str | None = None
        
        logger.info("KeycloakAdminClient inicializado - url=%s, realm=%s", config.url, config.target_realm)
    
    async def __aenter__(self) -> KeycloakAdminClient:
        """Context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Garante que o cliente HTTP está inicializado."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                timeout=httpx.Timeout(30.0),
            )
            logger.debug("Cliente HTTP criado")
    
    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("Cliente HTTP fechado")
    
    async def _get_admin_token(self) -> str:
        """Obtém token de admin do Keycloak."""
        await self._ensure_client()
        
        logger.debug("Obtendo token de admin")
        
        response = await self._client.post(
            f"/realms/{self.config.admin_realm}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": self.config.admin_username,
                "password": self.config.admin_password,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        
        self._access_token = data["access_token"]
        logger.debug("Token de admin obtido")
        
        return self._access_token
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """Faz requisição autenticada à Admin API."""
        await self._ensure_client()
        
        if not self._access_token:
            await self._get_admin_token()
        
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        
        response = await self._client.request(
            method=method,
            url=endpoint,
            json=data,
            params=params,
            headers=headers,
        )
        
        # Se 401, renovar token e tentar novamente
        if response.status_code == 401:
            logger.warning("Token expirado, renovando...")
            await self._get_admin_token()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            response = await self._client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=headers,
            )
        
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
        
        return response.json()
    
    async def get_user(self, user_id: str) -> KeycloakUser:
        """
        Obtém usuário por ID.
        
        Args:
            user_id: UUID do usuário no Keycloak
        
        Returns:
            KeycloakUser
        """
        logger.info("Buscando usuário: %s", user_id)
        
        data = await self._request(
            "GET",
            f"/admin/realms/{self.config.target_realm}/users/{user_id}",
        )

        return KeycloakUser(**data)

    async def list_users(
        self,
        max_results: int = 100,
        first: int = 0,
    ) -> list[KeycloakUser]:
        """
        Lista usuários do realm.

        Args:
            max_results: Número máximo de resultados
            first: Offset (paginação)

        Returns:
            Lista de KeycloakUser
        """
        logger.info("Listando usuários (max=%d, first=%d)", max_results, first)

        data = await self._request(
            "GET",
            f"/admin/realms/{self.config.target_realm}/users",
            params={"max": max_results, "first": first},
        )

        return [KeycloakUser(**user) for user in data]

    async def get_user_roles(self, user_id: str) -> list[str]:
        """
        Obtém roles de um usuário.

        Args:
            user_id: UUID do usuário

        Returns:
            Lista de nomes de roles
        """
        logger.info("Buscando roles do usuário: %s", user_id)

        # Realm roles
        realm_roles = await self._request(
            "GET",
            f"/admin/realms/{self.config.target_realm}/users/{user_id}/role-mappings/realm",
        )

        role_names = [role["name"] for role in realm_roles]

        logger.debug("Roles encontradas: %s", role_names)

        return role_names

    async def count_users(self) -> int:
        """
        Conta total de usuários no realm.

        Returns:
            Número de usuários
        """
        logger.info("Contando usuários")

        result = await self._request(
            "GET",
            f"/admin/realms/{self.config.target_realm}/users/count",
        )

        # A API retorna um número diretamente
        count = result if isinstance(result, int) else 0

        logger.info("Total de usuários: %d", count)

        return count

    async def get_all_users(self) -> list[KeycloakUser]:
        """
        Obtém todos os usuários do realm (com paginação).

        Returns:
            Lista completa de KeycloakUser
        """
        logger.info("Buscando todos os usuários")

        all_users = []
        batch_size = 100
        offset = 0

        while True:
            batch = await self.list_users(max_results=batch_size, first=offset)

            if not batch:
                break

            all_users.extend(batch)
            offset += batch_size

            logger.debug("Carregados %d usuários (total: %d)", len(batch), len(all_users))

            # Se retornou menos que batch_size, acabou
            if len(batch) < batch_size:
                break

        logger.info("Total de usuários carregados: %d", len(all_users))

        return all_users

