"""Contexto de tenant para requisicoes multi-tenant.

O TenantContext e um dataclass imutavel que carrega todas as informacoes
do tenant atual durante o ciclo de vida de uma requisicao HTTP.

Uso:
    # Criado automaticamente pelo tenant_middleware (intellicare-auth)
    ctx = TenantContext.from_jwt(jwt_payload)

    # Ou via FastAPI Depends
    from intellicare_auth import get_tenant_context
    @router.get("/data")
    async def get_data(ctx: TenantContext = Depends(get_tenant_context)):
        print(ctx.tenant_id)       # "hospital_einstein"
        print(ctx.tenant_schema)   # "tenant_hospital_einstein"
        print(ctx.is_multi_org)    # True se usuario tem multiplos tenants
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# Regex para validar tenant_id: alfanumerico + underscore, 3-100 chars
_TENANT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]{2,99}$")


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Contexto imutavel do tenant para a requisicao atual.

    Attributes:
        tenant_id: Identificador unico do tenant (slug)
        tenant_schema: Nome do schema PostgreSQL do tenant
        user_id: ID do usuario (sub do JWT)
        user_roles: Lista de roles do usuario
        available_tenants: Todos os tenants que o usuario tem acesso (multi-org)
    """

    tenant_id: str
    tenant_schema: str
    user_id: str
    user_roles: list[str] = field(default_factory=list)
    available_tenants: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valida o tenant_id apos criacao."""
        if self.tenant_id != "default" and not _TENANT_ID_PATTERN.match(self.tenant_id):
            raise ValueError(
                f"tenant_id invalido: '{self.tenant_id}'. "
                "Deve ser alfanumerico com underscore, 3-100 caracteres, "
                "iniciando com letra ou numero."
            )

    @classmethod
    def from_jwt(cls, payload: dict) -> TenantContext:
        """Cria TenantContext a partir do payload do JWT.

        Args:
            payload: Dicionario com claims do JWT Keycloak.
                     Espera: sub, tenant_id, tenants (array), realm_access.roles

        Returns:
            TenantContext preenchido com dados do JWT.
        """
        tenant_id = payload.get("tenant_id") or "default"
        tenants = payload.get("tenants", [])

        # Se tenant_id nao esta definido mas ha tenants, usar o primeiro
        # (cenario de auto-select quando ha apenas 1 tenant)
        if tenant_id == "default" and len(tenants) == 1:
            tenant_id = tenants[0]

        return cls(
            tenant_id=tenant_id,
            tenant_schema=f"tenant_{tenant_id}" if tenant_id != "default" else "public",
            user_id=payload.get("sub", ""),
            user_roles=cls._extract_roles(payload),
            available_tenants=tenants,
        )

    @property
    def is_multi_org(self) -> bool:
        """Retorna True se o usuario tem acesso a multiplos tenants."""
        return len(self.available_tenants) > 1

    @property
    def has_tenant_selected(self) -> bool:
        """Retorna True se um tenant esta selecionado (nao e 'default')."""
        return self.tenant_id != "default"

    @classmethod
    def default(cls) -> TenantContext:
        """Cria contexto para modo single-tenant (compatibilidade).

        Usado quando multi_tenant_enabled=False no BaseModuleConfig.
        Mapeia para o schema 'public' (comportamento original).
        """
        return cls(
            tenant_id="default",
            tenant_schema="public",
            user_id="system",
            user_roles=[],
            available_tenants=["default"],
        )

    @staticmethod
    def _extract_roles(payload: dict) -> list[str]:
        """Extrai roles do payload JWT (realm + resource access).

        Combina roles de:
        - realm_access.roles (roles globais do realm)
        - resource_access.{client}.roles (roles por client)
        """
        roles: list[str] = []

        # Roles do realm
        realm_access = payload.get("realm_access", {})
        roles.extend(realm_access.get("roles", []))

        # Roles de resource/client
        resource_access = payload.get("resource_access", {})
        for client_roles in resource_access.values():
            if isinstance(client_roles, dict):
                roles.extend(client_roles.get("roles", []))

        return list(set(roles))

    def __repr__(self) -> str:
        return (
            f"TenantContext(tenant_id='{self.tenant_id}', "
            f"schema='{self.tenant_schema}', "
            f"user='{self.user_id}', "
            f"multi_org={self.is_multi_org})"
        )
