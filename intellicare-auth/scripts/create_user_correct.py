#!/usr/bin/env python3
"""
Script CORRETO para criar usuário no realm bemcuidar
Usa a API REST diretamente
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
import requests
import urllib3

# Desabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"
USERNAME = "dr.silva@saudeplanner.com.br"
PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print(f"🔐 CRIANDO USUÁRIO NO REALM: {REALM_NAME}")
    print("=" * 80)
    print()
    
    try:
        # 1. Obter token de admin
        print("📡 Obtendo token de admin...")
        token_url = f"{KEYCLOAK_URL}realms/master/protocol/openid-connect/token"
        
        token_response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            },
            verify=False
        )
        
        if token_response.status_code != 200:
            print(f"❌ Erro ao obter token: {token_response.text}")
            sys.exit(1)
        
        admin_token = token_response.json()["access_token"]
        print("✅ Token obtido!")
        print()
        
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # 2. Verificar se usuário existe no realm bemcuidar
        print(f"🔍 Verificando usuário no realm {REALM_NAME}...")
        users_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users?username={USERNAME}&exact=true"
        
        users_response = requests.get(users_url, headers=headers, verify=False)
        users = users_response.json()
        
        if users:
            user_id = users[0]["id"]
            print(f"⚠️  Usuário já existe!")
            print(f"   ID: {user_id}")
            print()
            
            # Deletar
            print("🗑️  Deletando usuário existente...")
            delete_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users/{user_id}"
            delete_response = requests.delete(delete_url, headers=headers, verify=False)
            
            if delete_response.status_code == 204:
                print("✅ Usuário deletado!")
            else:
                print(f"⚠️  Erro ao deletar: {delete_response.status_code}")
            print()
        else:
            print(f"✅ Usuário não existe no realm {REALM_NAME}")
            print()
        
        # 3. Criar usuário no realm bemcuidar
        print(f"👤 Criando usuário: {USERNAME}")
        print(f"   Realm: {REALM_NAME}")
        print(f"   Senha: {PASSWORD}")
        print()
        
        create_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users"
        
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
        
        create_response = requests.post(
            create_url,
            json=user_data,
            headers=headers,
            verify=False
        )
        
        if create_response.status_code == 201:
            print("✅ Usuário criado com sucesso!")
            
            # Obter ID do usuário criado
            location = create_response.headers.get("Location")
            user_id = location.split("/")[-1] if location else None
            print(f"   ID: {user_id}")
            print()
            
            # 4. Atribuir role
            if user_id:
                print("🎭 Atribuindo role 'intellicare_doctor'...")
                
                # Buscar role
                role_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/roles/intellicare_doctor"
                role_response = requests.get(role_url, headers=headers, verify=False)
                
                if role_response.status_code == 200:
                    role = role_response.json()
                    
                    # Atribuir role
                    assign_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users/{user_id}/role-mappings/realm"
                    assign_response = requests.post(
                        assign_url,
                        json=[role],
                        headers=headers,
                        verify=False
                    )
                    
                    if assign_response.status_code == 204:
                        print("✅ Role atribuída!")
                    else:
                        print(f"⚠️  Erro ao atribuir role: {assign_response.status_code}")
                else:
                    print(f"⚠️  Role não encontrada: {role_response.status_code}")
        else:
            print(f"❌ Erro ao criar usuário: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            sys.exit(1)
        
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

