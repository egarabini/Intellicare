"""Exceções customizadas para intellicare-auth."""


class IntelliCareAuthError(Exception):
    """Exceção base para erros de autenticação IntelliCare."""

    pass


class AuthenticationError(IntelliCareAuthError):
    """Erro de autenticação - token inválido ou ausente."""

    pass


class AuthorizationError(IntelliCareAuthError):
    """Erro de autorização - usuário não tem permissão."""

    pass


class InvalidTokenError(AuthenticationError):
    """Token JWT inválido ou expirado."""

    pass


class KeycloakConnectionError(IntelliCareAuthError):
    """Erro de conexão com servidor Keycloak."""

    pass


class RoleNotFoundError(AuthorizationError):
    """Role requerida não encontrada no token do usuário."""

    pass

