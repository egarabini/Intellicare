#!/usr/bin/env python3
"""
Script para resetar senha de usuário no realm bemcuidar
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

# Configurações
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

# Usuário para resetar
USERNAME = "dr.silva@saudeplanner.com.br"
NEW_PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print("🔐 RESETANDO SENHA DE USUÁRIO")
    print("=" * 80)
    print()
    
    print(f"📡 Conectando ao Keycloak: {KEYCLOAK_URL}")
    print(f"   Realm: {REALM_NAME}")
    print(f"   Usuário: {USERNAME}")
    print()
    
    try:
        # Login no master realm
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=False
        )
        
        # Mudar para o realm bemcuidar
        keycloak_admin.realm_name = REALM_NAME
        
        print("✅ Conectado com sucesso!")
        print()
        
        # Buscar usuário
        print(f"🔍 Buscando usuário: {USERNAME}")
        users = keycloak_admin.get_users({"username": USERNAME})
        
        if not users:
            print(f"❌ Usuário não encontrado!")
            sys.exit(1)
        
        user_id = users[0]["id"]
        print(f"✅ Usuário encontrado! ID: {user_id}")
        print()
        
        # Resetar senha
        print(f"🔑 Resetando senha para: {NEW_PASSWORD}")
        keycloak_admin.set_user_password(
            user_id=user_id,
            password=NEW_PASSWORD,
            temporary=False
        )
        
        print("✅ Senha resetada com sucesso!")
        print()
        print("=" * 80)
        print("🎉 CONCLUÍDO!")
        print("=" * 80)
        print(f"Usuário: {USERNAME}")
        print(f"Senha: {NEW_PASSWORD}")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

