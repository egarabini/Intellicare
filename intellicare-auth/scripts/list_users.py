#!/usr/bin/env python3
"""
Script para listar usuários no realm bemcuidar
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

def main():
    print("=" * 80)
    print(f"👥 USUÁRIOS NO REALM: {REALM_NAME}")
    print("=" * 80)
    print()
    
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=False
        )
        keycloak_admin.realm_name = REALM_NAME
        
        # Listar todos os usuários
        users = keycloak_admin.get_users({})
        
        print(f"Total de usuários: {len(users)}")
        print()
        
        for user in users:
            username = user.get("username", "N/A")
            email = user.get("email", "N/A")
            enabled = user.get("enabled", False)
            user_id = user.get("id", "N/A")
            
            print(f"👤 {username}")
            print(f"   Email: {email}")
            print(f"   Enabled: {enabled}")
            print(f"   ID: {user_id}")
            
            # Buscar roles do usuário
            try:
                roles = keycloak_admin.get_realm_roles_of_user(user_id)
                if roles:
                    role_names = [r["name"] for r in roles]
                    print(f"   Roles: {', '.join(role_names)}")
            except:
                pass
            
            print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

