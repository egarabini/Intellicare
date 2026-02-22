"""
IntelliCare Auth - Biblioteca de autenticação Keycloak para módulos IntelliCare.

Fornece integração com Keycloak GSI (keycloak.gsi.srv.br) incluindo:
- Cliente Keycloak para validação de tokens
- Middleware FastAPI para autenticação
- Decorators para controle de acesso baseado em roles
- Cache JWKS para performance
- Middleware de tenant para multi-tenancy
"""

__version__ = "1.0.0"

from intellicare_auth.client import KeycloakClient
from intellicare_auth.config import KeycloakConfig
from intellicare_auth.decorators import requires_role, requires_any_role
from intellicare_auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    KeycloakConnectionError,
)
from intellicare_auth.middleware import get_current_user, get_optional_user
from intellicare_auth.tenant_middleware import (
    get_tenant_context,
    get_available_tenants,
    get_optional_tenant_context,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "KeycloakClient",
    # Config
    "KeycloakConfig",
    # Middleware
    "get_current_user",
    "get_optional_user",
    # Tenant Middleware (Multi-tenancy)
    "get_tenant_context",
    "get_available_tenants",
    "get_optional_tenant_context",
    # Decorators
    "requires_role",
    "requires_any_role",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "InvalidTokenError",
    "KeycloakConnectionError",
]
