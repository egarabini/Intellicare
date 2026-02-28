#!/usr/bin/env python3
"""
Script para deletar usuário do realm MASTER
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
USERNAME = "dr.silva@saudeplanner.com.br"

def main():
    print("=" * 80)
    print("🗑️  DELETANDO USUÁRIO DO REALM MASTER")
    print("=" * 80)
    print()
    
    try:
        # Conectar ao MASTER
        print("📡 Conectando ao realm MASTER...")
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",  # MASTER realm
            verify=False
        )
        print(f"✅ Conectado ao realm: {keycloak_admin.realm_name}")
        print()
        
        # Buscar usuário no MASTER
        print(f"🔍 Buscando usuário no MASTER: {USERNAME}")
        users = keycloak_admin.get_users({"username": USERNAME, "exact": True})
        
        if users:
            user_id = users[0]["id"]
            print(f"✅ Usuário encontrado no MASTER!")
            print(f"   ID: {user_id}")
            print(f"   Username: {users[0].get('username')}")
            print(f"   Email: {users[0].get('email')}")
            print()
            
            # Deletar
            print("🗑️  Deletando usuário do MASTER...")
            keycloak_admin.delete_user(user_id)
            print("✅ Usuário DELETADO do realm MASTER!")
            print()
            
            # Verificar
            print("🔍 Verificando deleção...")
            users = keycloak_admin.get_users({"username": USERNAME, "exact": True})
            
            if not users:
                print("✅ CONFIRMADO! Usuário NÃO existe mais no MASTER")
            else:
                print("⚠️  Usuário ainda existe no MASTER")
        else:
            print(f"✅ Usuário NÃO existe no realm MASTER")
        
        print()
        print("=" * 80)
        print("🎉 CONCLUÍDO!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

