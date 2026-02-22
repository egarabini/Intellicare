#!/usr/bin/env python3
"""
Script simples para criar usuários de teste no realm bemcuidar
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

# Configurações
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

def main():
    print("=" * 80)
    print("🔐 CRIANDO USUÁRIOS NO REALM BEMCUIDAR")
    print("=" * 80)
    print()
    
    try:
        # Conectar
        print(f"📡 Conectando ao Keycloak...")
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=False
        )
        keycloak_admin.realm_name = REALM_NAME
        print("✅ Conectado!")
        print()
        
        # Criar usuário dr.silva
        username = "dr.silva@saudeplanner.com.br"
        print(f"👤 Criando: {username}")
        
        try:
            user_id = keycloak_admin.create_user({
                "username": username,
                "email": username,
                "firstName": "Dr. João",
                "lastName": "Silva",
                "enabled": True,
                "emailVerified": True,
                "credentials": [{
                    "type": "password",
                    "value": "Test@123",
                    "temporary": False
                }]
            })
            
            print(f"   ✅ Criado! ID: {user_id}")
            
            # Atribuir role
            try:
                role = keycloak_admin.get_realm_role("intellicare_doctor")
                keycloak_admin.assign_realm_roles(user_id, [role])
                print(f"   ✅ Role 'intellicare_doctor' atribuída")
            except Exception as e:
                print(f"   ⚠️  Erro ao atribuir role: {e}")
            
        except Exception as e:
            if "409" in str(e) or "exists" in str(e).lower():
                print(f"   ⚠️  Usuário já existe")
            else:
                print(f"   ❌ Erro: {e}")
        
        print()
        
        # Criar usuário admin
        username = "admin@saudeplanner.com.br"
        print(f"👤 Criando: {username}")
        
        try:
            user_id = keycloak_admin.create_user({
                "username": username,
                "email": username,
                "firstName": "Admin",
                "lastName": "Sistema",
                "enabled": True,
                "emailVerified": True,
                "credentials": [{
                    "type": "password",
                    "value": "Test@123",
                    "temporary": False
                }]
            })
            
            print(f"   ✅ Criado! ID: {user_id}")
            
            # Atribuir role
            try:
                role = keycloak_admin.get_realm_role("intellicare_admin")
                keycloak_admin.assign_realm_roles(user_id, [role])
                print(f"   ✅ Role 'intellicare_admin' atribuída")
            except Exception as e:
                print(f"   ⚠️  Erro ao atribuir role: {e}")
            
        except Exception as e:
            if "409" in str(e) or "exists" in str(e).lower():
                print(f"   ⚠️  Usuário já existe")
            else:
                print(f"   ❌ Erro: {e}")
        
        print()
        print("=" * 80)
        print("✅ CONCLUÍDO!")
        print("=" * 80)
        print()
        print("Credenciais:")
        print("  • dr.silva@saudeplanner.com.br / Test@123")
        print("  • admin@saudeplanner.com.br / Test@123")
        print()
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

