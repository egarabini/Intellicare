#!/usr/bin/env python3
"""
Script para verificar e corrigir usuário
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"
USERNAME = "dr.silva@saudeplanner.com.br"
NEW_PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print("🔍 VERIFICANDO E CORRIGINDO USUÁRIO")
    print("=" * 80)
    print()
    
    try:
        # Conectar
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=False
        )
        keycloak_admin.realm_name = REALM_NAME
        
        print(f"✅ Conectado ao realm: {REALM_NAME}")
        print()
        
        # Buscar usuário
        print(f"🔍 Buscando usuário: {USERNAME}")
        users = keycloak_admin.get_users({"username": USERNAME})
        
        if not users:
            print(f"❌ Usuário NÃO encontrado no realm {REALM_NAME}!")
            print()
            print("Criando usuário...")
            
            user_id = keycloak_admin.create_user({
                "username": USERNAME,
                "email": USERNAME,
                "firstName": "Dr. João",
                "lastName": "Silva",
                "enabled": True,
                "emailVerified": True,
                "credentials": [{
                    "type": "password",
                    "value": NEW_PASSWORD,
                    "temporary": False
                }]
            })
            
            print(f"✅ Usuário criado! ID: {user_id}")
            
            # Atribuir role
            try:
                role = keycloak_admin.get_realm_role("intellicare_doctor")
                keycloak_admin.assign_realm_roles(user_id, [role])
                print(f"✅ Role 'intellicare_doctor' atribuída")
            except Exception as e:
                print(f"⚠️  Erro ao atribuir role: {e}")
            
        else:
            user = users[0]
            user_id = user["id"]
            
            print(f"✅ Usuário encontrado!")
            print(f"   ID: {user_id}")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Enabled: {user.get('enabled')}")
            print(f"   Email Verified: {user.get('emailVerified')}")
            print()
            
            # Resetar senha
            print(f"🔑 Resetando senha para: {NEW_PASSWORD}")
            keycloak_admin.set_user_password(
                user_id=user_id,
                password=NEW_PASSWORD,
                temporary=False
            )
            print("✅ Senha resetada!")
            print()
            
            # Garantir que está habilitado
            print("🔧 Garantindo que usuário está habilitado...")
            keycloak_admin.update_user(user_id, {
                "enabled": True,
                "emailVerified": True
            })
            print("✅ Usuário habilitado!")
        
        print()
        print("=" * 80)
        print("🎉 CONCLUÍDO!")
        print("=" * 80)
        print()
        print(f"Usuário: {USERNAME}")
        print(f"Senha: {NEW_PASSWORD}")
        print(f"Realm: {REALM_NAME}")
        print()
        print("Agora teste novamente!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

