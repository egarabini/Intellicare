#!/usr/bin/env python3
"""
Script para criar TODOS os usuários de teste no realm bemcuidar
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import urllib3

# Desabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

# Todos os usuários
USERS = [
    {
        "username": "admin@saudeplanner.com.br",
        "email": "admin@saudeplanner.com.br",
        "firstName": "Admin",
        "lastName": "Sistema",
        "role": "intellicare_admin"
    },
    {
        "username": "dr.silva@saudeplanner.com.br",
        "email": "dr.silva@saudeplanner.com.br",
        "firstName": "Dr. João",
        "lastName": "Silva",
        "role": "intellicare_doctor"
    },
    {
        "username": "nurse.santos@saudeplanner.com.br",
        "email": "nurse.santos@saudeplanner.com.br",
        "firstName": "Maria",
        "lastName": "Santos",
        "role": "intellicare_nurse"
    },
    {
        "username": "nutritionist.lima@saudeplanner.com.br",
        "email": "nutritionist.lima@saudeplanner.com.br",
        "firstName": "Ana",
        "lastName": "Lima",
        "role": "intellicare_nutritionist"
    },
    {
        "username": "patient.oliveira@saudeplanner.com.br",
        "email": "patient.oliveira@saudeplanner.com.br",
        "firstName": "Carlos",
        "lastName": "Oliveira",
        "role": "intellicare_patient"
    }
]

PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print(f"🔐 CRIANDO TODOS OS USUÁRIOS NO REALM: {REALM_NAME}")
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
        
        created_count = 0
        skipped_count = 0
        
        # 2. Criar cada usuário
        for user_info in USERS:
            username = user_info["username"]
            role_name = user_info["role"]
            
            print(f"👤 Processando: {username}")
            
            # Verificar se existe
            users_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users?username={username}&exact=true"
            users_response = requests.get(users_url, headers=headers, verify=False)
            users = users_response.json()
            
            if users:
                print(f"   ⚠️  Usuário já existe, pulando...")
                skipped_count += 1
                print()
                continue
            
            # Criar usuário
            create_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/users"
            
            user_data = {
                "username": username,
                "email": user_info["email"],
                "firstName": user_info["firstName"],
                "lastName": user_info["lastName"],
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
                # Obter ID do usuário criado
                location = create_response.headers.get("Location")
                user_id = location.split("/")[-1] if location else None
                
                print(f"   ✅ Criado! ID: {user_id}")
                
                # Atribuir role
                if user_id and role_name:
                    # Buscar role
                    role_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/roles/{role_name}"
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
                            print(f"   ✅ Role '{role_name}' atribuída")
                        else:
                            print(f"   ⚠️  Erro ao atribuir role: {assign_response.status_code}")
                    else:
                        print(f"   ⚠️  Role '{role_name}' não encontrada")
                
                created_count += 1
            else:
                print(f"   ❌ Erro ao criar: {create_response.status_code}")
                print(f"   Response: {create_response.text}")
            
            print()
        
        # Resumo
        print("=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        print(f"✅ Usuários criados: {created_count}")
        print(f"⚠️  Usuários já existentes: {skipped_count}")
        print(f"📈 Total processado: {len(USERS)}")
        print()
        
        if created_count > 0 or skipped_count > 0:
            print("🎉 USUÁRIOS DISPONÍVEIS NO REALM BEMCUIDAR!")
            print()
            print("📝 Credenciais (senha para todos: Test@123):")
            for user in USERS:
                print(f"   • {user['username']} - Role: {user['role']}")
            print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

