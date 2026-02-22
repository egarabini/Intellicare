"""Configurações para integração com Keycloak."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakConfig(BaseSettings):
    """
    Configurações do Keycloak.
    
    Carrega automaticamente de variáveis de ambiente com prefixo KEYCLOAK_.
    """

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Servidor Keycloak
    server_url: str = Field(
        default="https://keycloak.gsi.srv.br/auth",
        description="URL do servidor Keycloak (com /auth)",
    )

    realm: str = Field(
        default="saudeplanner.com.br",
        description="Nome do realm Keycloak",
    )

    # Client credentials
    client_id: str = Field(
        ...,
        description="Client ID do módulo no Keycloak",
    )

    client_secret: Optional[str] = Field(
        default=None,
        description="Client Secret (para confidential clients)",
    )

    # Configurações de cache
    jwks_cache_ttl: int = Field(
        default=300,
        description="TTL do cache JWKS em segundos (padrão: 5 minutos)",
    )

    token_cache_ttl: int = Field(
        default=60,
        description="TTL do cache de tokens validados em segundos (padrão: 1 minuto)",
    )

    # Configurações de timeout
    connection_timeout: int = Field(
        default=10,
        description="Timeout de conexão HTTP em segundos",
    )

    read_timeout: int = Field(
        default=30,
        description="Timeout de leitura HTTP em segundos",
    )

    # Configurações de validação
    verify_ssl: bool = Field(
        default=True,
        description="Verificar certificado SSL do Keycloak",
    )

    validate_audience: bool = Field(
        default=True,
        description="Validar audience (aud) no token JWT",
    )

    validate_issuer: bool = Field(
        default=True,
        description="Validar issuer (iss) no token JWT",
    )

    # Configurações de retry
    max_retries: int = Field(
        default=3,
        description="Número máximo de tentativas em caso de erro",
    )

    retry_delay: float = Field(
        default=1.0,
        description="Delay entre tentativas em segundos",
    )

    @property
    def realm_url(self) -> str:
        """URL completa do realm."""
        return f"{self.server_url}/realms/{self.realm}"

    @property
    def token_endpoint(self) -> str:
        """Endpoint de token OAuth2."""
        return f"{self.realm_url}/protocol/openid-connect/token"

    @property
    def userinfo_endpoint(self) -> str:
        """Endpoint de informações do usuário."""
        return f"{self.realm_url}/protocol/openid-connect/userinfo"

    @property
    def jwks_uri(self) -> str:
        """URI do JWKS (JSON Web Key Set)."""
        return f"{self.realm_url}/protocol/openid-connect/certs"

    @property
    def introspection_endpoint(self) -> str:
        """Endpoint de introspecção de token."""
        return f"{self.realm_url}/protocol/openid-connect/token/introspect"

    @property
    def issuer(self) -> str:
        """Issuer esperado nos tokens JWT."""
        return self.realm_url

    def __repr__(self) -> str:
        """Representação segura (sem expor secrets)."""
        return (
            f"KeycloakConfig(server_url='{self.server_url}', "
            f"realm='{self.realm}', "
            f"client_id='{self.client_id}', "
            f"client_secret='***')"
        )

