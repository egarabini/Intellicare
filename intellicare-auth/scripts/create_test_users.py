"""Script para criar usuários de teste no Keycloak."""

import os

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection


# Configuração do Keycloak
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
REALM_NAME = "bemcuidar"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "Crazy#57LB")

# Usuários de teste
TEST_USERS = [
    {
        "username": "dr.silva@saudeplanner.com.br",
        "email": "dr.silva@saudeplanner.com.br",
        "firstName": "João",
        "lastName": "Silva",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "specialty": ["Cardiologia"],
            "license_number": ["CRM-SP-123456"],
            "department": ["Cardiologia"],
        },
        "realmRoles": ["intellicare_doctor"],
    },
    {
        "username": "enf.maria@saudeplanner.com.br",
        "email": "enf.maria@saudeplanner.com.br",
        "firstName": "Maria",
        "lastName": "Santos",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "department": ["Enfermagem"],
        },
        "realmRoles": ["intellicare_nurse"],
    },
    {
        "username": "nutri.ana@saudeplanner.com.br",
        "email": "nutri.ana@saudeplanner.com.br",
        "firstName": "Ana",
        "lastName": "Costa",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "license_number": ["CRN-SP-789012"],
            "department": ["Nutrição"],
        },
        "realmRoles": ["intellicare_nutritionist"],
    },
    {
        "username": "coord.pedro@saudeplanner.com.br",
        "email": "coord.pedro@saudeplanner.com.br",
        "firstName": "Pedro",
        "lastName": "Oliveira",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "attributes": {
            "hospital_id": ["HOSP001"],
            "department": ["Coordenação de Cuidados"],
        },
        "realmRoles": ["intellicare_care_coordinator"],
    },
    {
        "username": "paciente.jose@saudeplanner.com.br",
        "email": "paciente.jose@saudeplanner.com.br",
        "firstName": "José",
        "lastName": "Ferreira",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "Test@123", "temporary": False}],
        "attributes": {
            "hospital_id": ["HOSP001"],
        },
        "realmRoles": ["intellicare_patient"],
    },
]


def create_test_users():
    """Cria usuários de teste no Keycloak."""
    
    print("👥 CRIAR USUÁRIOS DE TESTE - KEYCLOAK")
    print("=" * 60)
    
    # Conectar ao Keycloak
    print(f"\n📡 Conectando ao Keycloak: {KEYCLOAK_URL}")
    
    try:
        keycloak_connection = KeycloakOpenIDConnection(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",  # Login no master para ter permissões admin
            verify=True,
        )

        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        keycloak_admin.realm_name = REALM_NAME  # Mas trabalhar no realm bemcuidar
        
        print("✅ Conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Criar usuários
    print(f"\n👤 Criando Usuários de Teste...")
    print("-" * 60)
    
    created_users = []
    
    for user_data in TEST_USERS:
        username = user_data["username"]
        print(f"\n📝 Criando: {username}")
        
        try:
            # Criar usuário
            user_id = keycloak_admin.create_user(user_data, exist_ok=False)
            print(f"   ✅ Usuário criado: {user_id}")
            
            # Adicionar roles
            roles = user_data.get("realmRoles", [])
            for role_name in roles:
                try:
                    role = keycloak_admin.get_realm_role(role_name)
                    keycloak_admin.assign_realm_roles(user_id, [role])
                    print(f"   ✅ Role atribuída: {role_name}")
                except Exception as e:
                    print(f"   ❌ Erro ao atribuir role {role_name}: {e}")
            
            created_users.append(username)
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ⚠️  Usuário já existe: {username}")
            else:
                print(f"   ❌ Erro ao criar usuário: {e}")
    
    # Resumo
    print(f"\n" + "=" * 60)
    print(f"✅ USUÁRIOS CRIADOS COM SUCESSO!")
    print(f"=" * 60)
    
    print(f"\n📊 Resumo:")
    print(f"   - Usuários criados: {len(created_users)}/{len(TEST_USERS)}")
    
    print(f"\n👥 Credenciais de Teste:")
    print(f"   Senha padrão: Test@123")
    print(f"\n   Usuários:")
    for user in TEST_USERS:
        roles = ", ".join(user.get("realmRoles", []))
        print(f"   - {user['username']} ({roles})")
    
    print(f"\n🧪 Testar Login:")
    print(f"   curl -X POST {KEYCLOAK_URL}realms/{REALM_NAME}/protocol/openid-connect/token \\")
    print(f"     -d 'grant_type=password' \\")
    print(f"     -d 'client_id=intellicare-core' \\")
    print(f"     -d 'username=dr.silva@saudeplanner.com.br' \\")
    print(f"     -d 'password=Test@123'")


if __name__ == "__main__":
    create_test_users()

