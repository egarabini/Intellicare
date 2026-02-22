#!/usr/bin/env python3
"""
Script para FORÇAR criação de usuário no realm bemcuidar
Deleta se existir e recria
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"  # EXPLICITAMENTE bemcuidar
USERNAME = "dr.silva@saudeplanner.com.br"
PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print(f"🔐 FORÇANDO CRIAÇÃO DE USUÁRIO NO REALM: {REALM_NAME}")
    print("=" * 80)
    print()
    
    try:
        # Conectar ao master
        print("📡 Conectando ao Keycloak (master realm)...")
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",  # Login no master
            verify=False
        )
        print("✅ Conectado ao master!")
        print()
        
        # MUDAR EXPLICITAMENTE PARA BEMCUIDAR
        print(f"🔄 Mudando para realm: {REALM_NAME}")
        keycloak_admin.realm_name = REALM_NAME
        print(f"✅ Agora trabalhando no realm: {keycloak_admin.realm_name}")
        print()
        
        # Verificar se usuário existe
        print(f"🔍 Verificando se usuário existe: {USERNAME}")
        users = keycloak_admin.get_users({"username": USERNAME, "exact": True})
        
        if users:
            user_id = users[0]["id"]
            print(f"⚠️  Usuário JÁ EXISTE no realm {REALM_NAME}")
            print(f"   ID: {user_id}")
            print()
            
            # Deletar usuário existente
            print("🗑️  Deletando usuário existente...")
            keycloak_admin.delete_user(user_id)
            print("✅ Usuário deletado!")
            print()
        else:
            print(f"✅ Usuário NÃO existe no realm {REALM_NAME}")
            print()
        
        # Criar usuário NOVO
        print(f"👤 Criando usuário: {USERNAME}")
        print(f"   Realm: {REALM_NAME}")
        print(f"   Senha: {PASSWORD}")
        print()
        
        user_data = {
            "username": USERNAME,
            "email": USERNAME,
            "firstName": "Dr. João",
            "lastName": "Silva",
            "enabled": True,
            "emailVerified": True,
            "credentials": [{
                "type": "password",
                "value": PASSWORD,
                "temporary": False
            }]
        }
        
        user_id = keycloak_admin.create_user(user_data)
        print(f"✅ Usuário criado com sucesso!")
        print(f"   ID: {user_id}")
        print()
        
        # Atribuir role
        print("🎭 Atribuindo role 'intellicare_doctor'...")
        try:
            role = keycloak_admin.get_realm_role("intellicare_doctor")
            keycloak_admin.assign_realm_roles(user_id, [role])
            print("✅ Role atribuída!")
        except Exception as e:
            print(f"⚠️  Erro ao atribuir role: {e}")
        
        print()
        
        # Verificar criação
        print("🔍 Verificando criação...")
        users = keycloak_admin.get_users({"username": USERNAME, "exact": True})
        
        if users:
            user = users[0]
            print("✅ CONFIRMADO! Usuário existe no realm bemcuidar:")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Enabled: {user.get('enabled')}")
            print(f"   Email Verified: {user.get('emailVerified')}")
            
            # Verificar roles
            try:
                roles = keycloak_admin.get_realm_roles_of_user(user["id"])
                if roles:
                    role_names = [r["name"] for r in roles]
                    print(f"   Roles: {', '.join(role_names)}")
            except:
                pass
        else:
            print("❌ ERRO! Usuário NÃO foi criado!")
        
        print()
        print("=" * 80)
        print("🎉 CONCLUÍDO!")
        print("=" * 80)
        print()
        print(f"Realm: {REALM_NAME}")
        print(f"Usuário: {USERNAME}")
        print(f"Senha: {PASSWORD}")
        print()
        print("Agora teste o login!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

