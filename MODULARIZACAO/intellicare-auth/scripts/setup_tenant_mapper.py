"""Script para configurar Keycloak com mappers de multi-tenancy.

Cria os protocol mappers necessarios no realm Keycloak para incluir
tenant_id e tenants[] nos tokens JWT.

Uso:
    python setup_tenant_mapper.py

Requisitos:
    - python-keycloak
    - Variaveis de ambiente configuradas (ver abaixo)

Variaveis de ambiente:
    KEYCLOAK_URL: URL do servidor Keycloak
    KEYCLOAK_REALM: Nome do realm (default: bemcuidar)
    KEYCLOAK_ADMIN_USER: Usuario admin
    KEYCLOAK_ADMIN_PASSWORD: Senha admin
    KEYCLOAK_CLIENT_ID: Client ID do portal (default: intellicare-portal)
"""

from __future__ import annotations

import os
import sys

from keycloak import KeycloakAdmin


def get_keycloak_admin() -> KeycloakAdmin:
    """Cria client admin do Keycloak."""
    return KeycloakAdmin(
        server_url=os.environ.get("KEYCLOAK_URL", "https://keycloak.gsi.srv.br"),
        username=os.environ.get("KEYCLOAK_ADMIN_USER", "admin"),
        password=os.environ.get("KEYCLOAK_ADMIN_PASSWORD", ""),
        realm_name=os.environ.get("KEYCLOAK_REALM", "bemcuidar"),
        verify=True,
    )


def create_tenant_id_mapper(admin: KeycloakAdmin, client_id: str) -> None:
    """Cria mapper para tenant_id no token."""
    mapper_payload = {
        "name": "tenant_id",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "tenant_id",
            "claim.name": "tenant_id",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
            "multivalued": "false",
        },
    }

    try:
        admin.add_mapper_to_client(client_id, mapper_payload)
        print("✅ Mapper 'tenant_id' criado com sucesso")
    except Exception as e:
        if "409" in str(e) or "Conflict" in str(e):
            print("ℹ️  Mapper 'tenant_id' já existe")
        else:
            raise


def create_tenants_mapper(admin: KeycloakAdmin, client_id: str) -> None:
    """Cria mapper para tenants[] (array de tenants autorizados) no token."""
    mapper_payload = {
        "name": "tenants",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "tenants",
            "claim.name": "tenants",
            "jsonType.label": "JSON",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
            "multivalued": "true",
        },
    }

    try:
        admin.add_mapper_to_client(client_id, mapper_payload)
        print("✅ Mapper 'tenants' (multivalued) criado com sucesso")
    except Exception as e:
        if "409" in str(e) or "Conflict" in str(e):
            print("ℹ️  Mapper 'tenants' já existe")
        else:
            raise


def setup_token_exchange(admin: KeycloakAdmin, client_id: str) -> None:
    """Habilita Token Exchange no client.

    Nota: Token Exchange requer Keycloak 24+ e configuracao manual
    do SPI para validar tenant_id contra o array tenants[].
    """
    print("ℹ️  Token Exchange requer configuração manual no Keycloak Admin Console:")
    print(f"   1. Ir em Clients → {client_id}")
    print("   2. Aba 'Advanced' → habilitar 'Token Exchange'")
    print("   3. Configurar policy de Token Exchange")
    print("   4. Implantar SPI customizado para validar tenant_id vs tenants[]")


def main() -> None:
    """Executa a configuracao completa dos mappers."""
    print("🔧 Configurando Keycloak para multi-tenancy...")
    print()

    admin = get_keycloak_admin()

    # Obter client ID interno
    portal_client_name = os.environ.get("KEYCLOAK_CLIENT_ID", "intellicare-portal")
    client_id = admin.get_client_id(portal_client_name)

    if not client_id:
        print(f"❌ Client '{portal_client_name}' não encontrado no realm")
        sys.exit(1)

    print(f"📋 Client: {portal_client_name} (id: {client_id})")
    print()

    # Criar mappers
    create_tenant_id_mapper(admin, client_id)
    create_tenants_mapper(admin, client_id)
    print()

    # Instruções para Token Exchange
    setup_token_exchange(admin, client_id)
    print()

    print("✅ Configuração de Keycloak multi-tenancy concluída!")


if __name__ == "__main__":
    main()
