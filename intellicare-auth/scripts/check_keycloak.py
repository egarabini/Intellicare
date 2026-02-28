#!/usr/bin/env python3
"""
Script para diagnosticar conexão com Keycloak e listar realms disponíveis.
"""

import os
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection

# Configuração
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "Crazy#57LB")

print("🔍 DIAGNÓSTICO KEYCLOAK")
print("=" * 60)
print(f"\n📡 URL: {KEYCLOAK_URL}")
print(f"👤 Usuário: {ADMIN_USERNAME}")

# Tentar diferentes realms
realms_to_try = ["master", "saudeplanner.com.br", "gsisaude", "bemcuidar"]

for realm in realms_to_try:
    print(f"\n🔐 Tentando realm: {realm}")
    try:
        connection = KeycloakOpenIDConnection(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name=realm,
            verify=True,
        )
        
        admin = KeycloakAdmin(connection=connection)
        
        print(f"   ✅ Conectado com sucesso ao realm '{realm}'!")
        
        # Tentar listar realms
        try:
            realms = admin.get_realms()
            print(f"\n📋 Realms disponíveis:")
            for r in realms:
                print(f"   - {r['realm']} (enabled: {r.get('enabled', 'N/A')})")
        except Exception as e:
            print(f"   ⚠️  Não foi possível listar realms: {e}")
        
        # Tentar listar clients no realm atual
        try:
            clients = admin.get_clients()
            print(f"\n📦 Clients no realm '{realm}': {len(clients)} encontrados")
            for client in clients[:5]:  # Mostrar apenas os 5 primeiros
                print(f"   - {client.get('clientId', 'N/A')}")
            if len(clients) > 5:
                print(f"   ... e mais {len(clients) - 5} clients")
        except Exception as e:
            print(f"   ⚠️  Não foi possível listar clients: {e}")
        
        break  # Se conectou com sucesso, parar
        
    except Exception as e:
        print(f"   ❌ Falha: {e}")

print("\n" + "=" * 60)
print("✅ Diagnóstico concluído!")

