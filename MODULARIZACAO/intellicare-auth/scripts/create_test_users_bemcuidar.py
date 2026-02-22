#!/usr/bin/env python3
"""
Script para criar usuários de teste no realm bemcuidar
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

# Configurações
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

# Usuários de teste
TEST_USERS = [
    {
        "username": "admin@saudeplanner.com.br",
        "email": "admin@saudeplanner.com.br",
        "firstName": "Admin",
        "lastName": "Sistema",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "roles": ["intellicare_admin"]
    },
    {
        "username": "dr.silva@saudeplanner.com.br",
        "email": "dr.silva@saudeplanner.com.br",
        "firstName": "Dr. João",
        "lastName": "Silva",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "roles": ["intellicare_doctor"],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "specialty": ["Cardiologia"],
            "license_number": ["CRM12345"]
        }
    },
    {
        "username": "nurse.santos@saudeplanner.com.br",
        "email": "nurse.santos@saudeplanner.com.br",
        "firstName": "Maria",
        "lastName": "Santos",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "roles": ["intellicare_nurse"],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "department": ["UTI"],
            "license_number": ["COREN67890"]
        }
    },
    {
        "username": "nutritionist.lima@saudeplanner.com.br",
        "email": "nutritionist.lima@saudeplanner.com.br",
        "firstName": "Ana",
        "lastName": "Lima",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "roles": ["intellicare_nutritionist"],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "license_number": ["CRN11223"]
        }
    },
    {
        "username": "patient.oliveira@saudeplanner.com.br",
        "email": "patient.oliveira@saudeplanner.com.br",
        "firstName": "Carlos",
        "lastName": "Oliveira",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "roles": ["intellicare_patient"],
        "attributes": {
            "patient_id": ["PAT001"],
            "cpf": ["12345678900"]
        }
    }
]

def main():
    print("=" * 80)
    print("🔐 CRIANDO USUÁRIOS DE TESTE NO REALM BEMCUIDAR")
    print("=" * 80)
    print()
    
    # Conectar ao Keycloak
    print(f"📡 Conectando ao Keycloak: {KEYCLOAK_URL}")
    print(f"   Realm: {REALM_NAME}")
    print()
    
    try:
        # Login no master realm para ter acesso admin
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",  # Login no master
            verify=False
        )
        
        # Mudar para o realm bemcuidar
        keycloak_admin.realm_name = REALM_NAME
        
        print("✅ Conectado com sucesso!")
        print()
        
        # Criar usuários
        created_count = 0
        skipped_count = 0
        
        for user_data in TEST_USERS:
            username = user_data["username"]
            print(f"👤 Criando usuário: {username}")

            try:
                # Verificar se usuário já existe
                existing_users = keycloak_admin.get_users({"username": username})

                if existing_users:
                    print(f"   ⚠️  Usuário já existe, pulando...")
                    skipped_count += 1
                    continue

                # Extrair roles antes de criar (não pode ser passado no create_user)
                roles = user_data.pop("roles", [])

                # Criar usuário
                user_id = keycloak_admin.create_user(user_data)
                print(f"   ✅ Usuário criado com ID: {user_id}")

                # Atribuir roles
                if roles:
                    for role_name in roles:
                        try:
                            # Buscar role
                            role = keycloak_admin.get_realm_role(role_name)

                            # Atribuir role ao usuário
                            keycloak_admin.assign_realm_roles(user_id, [role])
                            print(f"   ✅ Role atribuída: {role_name}")

                        except KeycloakError as e:
                            print(f"   ⚠️  Erro ao atribuir role {role_name}: {e}")

                created_count += 1
                print()

            except KeycloakError as e:
                print(f"   ❌ Erro ao criar usuário: {e}")
                print()
        
        # Resumo
        print("=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        print(f"✅ Usuários criados: {created_count}")
        print(f"⚠️  Usuários já existentes: {skipped_count}")
        print(f"📈 Total processado: {len(TEST_USERS)}")
        print()
        
        if created_count > 0:
            print("🎉 USUÁRIOS CRIADOS COM SUCESSO!")
            print()
            print("📝 Credenciais de acesso:")
            print("   Senha para todos: Test@123")
            print()
            print("👥 Usuários disponíveis:")
            for user in TEST_USERS:
                roles = ", ".join(user.get("roles", []))
                print(f"   • {user['username']} - Roles: {roles}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

