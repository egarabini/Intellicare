#!/usr/bin/env python3
"""Script para atribuir roles aos usuários existentes no Keycloak."""

import os
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection

# Configuração do Keycloak
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
REALM_NAME = "bemcuidar"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "Crazy#57LB")

# Mapeamento usuário -> roles
USER_ROLES = {
    "dr.silva@saudeplanner.com.br": ["intellicare_doctor"],
    "enf.maria@saudeplanner.com.br": ["intellicare_nurse"],
    "nutri.ana@saudeplanner.com.br": ["intellicare_nutritionist"],
    "coord.pedro@saudeplanner.com.br": ["intellicare_care_coordinator"],
    "paciente.jose@saudeplanner.com.br": ["intellicare_patient"],
}


def assign_roles():
    """Atribui roles aos usuários existentes."""
    
    print("🔐 ATRIBUIR ROLES AOS USUÁRIOS")
    print("=" * 60)
    
    # Conectar ao Keycloak
    print(f"\n📡 Conectando ao Keycloak: {KEYCLOAK_URL}")
    
    try:
        keycloak_connection = KeycloakOpenIDConnection(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=True,
        )
        
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        keycloak_admin.realm_name = REALM_NAME
        
        print("✅ Conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Atribuir roles
    print(f"\n👤 Atribuindo Roles...")
    print("-" * 60)
    
    for username, role_names in USER_ROLES.items():
        print(f"\n📝 Processando: {username}")
        
        try:
            # Buscar usuário
            users = keycloak_admin.get_users({"username": username})
            if not users:
                print(f"   ❌ Usuário não encontrado: {username}")
                continue
            
            user_id = users[0]["id"]
            print(f"   ✅ Usuário encontrado: {user_id}")
            
            # Atribuir roles
            for role_name in role_names:
                try:
                    role = keycloak_admin.get_realm_role(role_name)
                    keycloak_admin.assign_realm_roles(user_id, [role])
                    print(f"   ✅ Role atribuída: {role_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "already assigned" in str(e).lower():
                        print(f"   ⚠️  Role já atribuída: {role_name}")
                    else:
                        print(f"   ❌ Erro ao atribuir role {role_name}: {e}")
            
        except Exception as e:
            print(f"   ❌ Erro ao processar usuário: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ROLES ATRIBUÍDAS COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    assign_roles()

