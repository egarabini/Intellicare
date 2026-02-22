#!/usr/bin/env python3
"""Script para listar roles no Keycloak."""

import os
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection

# Configuração
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
REALM_NAME = "bemcuidar"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "Crazy#57LB")

print("🔍 LISTAR ROLES NO KEYCLOAK")
print("=" * 60)

try:
    connection = KeycloakOpenIDConnection(
        server_url=KEYCLOAK_URL,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        realm_name="master",
        verify=True,
    )
    
    admin = KeycloakAdmin(connection=connection)
    admin.realm_name = REALM_NAME
    
    print(f"✅ Conectado ao realm: {REALM_NAME}")
    
    # Listar roles
    roles = admin.get_realm_roles()
    
    print(f"\n📋 Roles encontradas: {len(roles)}")
    print("-" * 60)
    
    for role in roles:
        print(f"   - {role['name']}")
        if role.get('description'):
            print(f"     Descrição: {role['description']}")
    
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "=" * 60)

