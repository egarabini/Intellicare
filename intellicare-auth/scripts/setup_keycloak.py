"""Script para configurar Keycloak automaticamente para IntelliCare."""

import json
import os
from typing import Dict, List

import httpx
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection


# Configuração do Keycloak
KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
REALM_NAME = "bemcuidar"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "Crazy#57LB")

# Módulos IntelliCare
MODULES = [
    {"client_id": "intellicare-core", "name": "IntelliCare Core", "port": 8000},
    {"client_id": "intellicare-wanda", "name": "IntelliCare Wanda - Orchestrator", "port": 8007},
    {"client_id": "intellicare-florence", "name": "IntelliCare Florence - Clinical Analysis", "port": 8001},
    {"client_id": "intellicare-oswaldo", "name": "IntelliCare Oswaldo - Chronic Diseases", "port": 8002},
    {"client_id": "intellicare-zilda", "name": "IntelliCare Zilda - CNES/Territorial", "port": 8004},
    {"client_id": "intellicare-geralda", "name": "IntelliCare Geralda - Care Plans", "port": 8005},
    {"client_id": "intellicare-donabedian", "name": "IntelliCare Donabedian - Quality Assessment", "port": 8003},
    {"client_id": "intellicare-portal", "name": "IntelliCare Portal - Web Frontend", "port": 3000},
    {"client_id": "intellicare-comunicacao", "name": "IntelliCare Comunicação - Matrix", "port": 8011},
]

# Roles IntelliCare
ROLES = [
    {"name": "intellicare_admin", "description": "Administrador geral do IntelliCare"},
    {"name": "intellicare_hospital_admin", "description": "Administrador de hospital"},
    {"name": "intellicare_doctor", "description": "Médico"},
    {"name": "intellicare_nurse", "description": "Enfermeiro(a)"},
    {"name": "intellicare_nutritionist", "description": "Nutricionista"},
    {"name": "intellicare_care_coordinator", "description": "Coordenador de cuidado"},
    {"name": "intellicare_patient", "description": "Paciente"},
]

# Protocol Mappers
PROTOCOL_MAPPERS = [
    {
        "name": "hospital_id",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "hospital_id",
            "claim.name": "hospital_id",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
        },
    },
    {
        "name": "specialty",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "specialty",
            "claim.name": "specialty",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
        },
    },
    {
        "name": "license_number",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "license_number",
            "claim.name": "license_number",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
        },
    },
    {
        "name": "department",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {
            "user.attribute": "department",
            "claim.name": "department",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
        },
    },
]


def setup_keycloak():
    """Configura Keycloak automaticamente."""
    
    print("🔐 SETUP KEYCLOAK INTELLICARE")
    print("=" * 60)
    
    # Conectar ao Keycloak
    print(f"\n📡 Conectando ao Keycloak: {KEYCLOAK_URL}")
    print(f"   Realm: {REALM_NAME}")
    
    try:
        keycloak_connection = KeycloakOpenIDConnection(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",  # Login no master realm com admin
            verify=True,
        )

        keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
        keycloak_admin.realm_name = REALM_NAME  # Mas trabalhar no realm bemcuidar
        
        print("✅ Conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("\n💡 Verifique:")
        print("   - URL do Keycloak está correta")
        print("   - Credenciais de admin estão corretas")
        print("   - Keycloak está acessível")
        return
    
    # Criar roles
    print(f"\n🎭 Criando Roles...")
    print("-" * 60)
    
    created_roles = []
    for role in ROLES:
        try:
            keycloak_admin.create_realm_role(
                payload={"name": role["name"], "description": role["description"]},
                skip_exists=True,
            )
            print(f"✅ Role criada: {role['name']}")
            created_roles.append(role["name"])
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"⚠️  Role já existe: {role['name']}")
                created_roles.append(role["name"])
            else:
                print(f"❌ Erro ao criar role {role['name']}: {e}")
    
    print(f"\n✅ {len(created_roles)}/{len(ROLES)} roles configuradas")
    
    # Criar clients
    print(f"\n🔧 Criando Clients...")
    print("-" * 60)
    
    client_secrets = {}
    
    for module in MODULES:
        client_id = module["client_id"]
        print(f"\n📦 Configurando: {client_id}")
        
        # Configuração do client
        client_config = {
            "clientId": client_id,
            "name": module["name"],
            "description": f"Módulo IntelliCare - {module['name']}",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "redirectUris": [
                f"http://localhost:{module['port']}/*",
                f"https://{client_id.replace('intellicare-', '')}.gsi.srv.br/*",
            ],
            "webOrigins": [
                f"http://localhost:{module['port']}",
                f"https://{client_id.replace('intellicare-', '')}.gsi.srv.br",
            ],
            "publicClient": False,
            "protocol": "openid-connect",
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "authorizationServicesEnabled": False,
        }

        try:
            # Criar client
            client_uuid = keycloak_admin.create_client(payload=client_config, skip_exists=False)
            print(f"   ✅ Client criado")

            # Obter client secret
            client_secret = keycloak_admin.get_client_secrets(client_uuid)
            secret = client_secret.get("value")
            client_secrets[client_id] = secret
            print(f"   🔑 Secret: {secret[:20]}...")

            # Adicionar protocol mappers
            for mapper in PROTOCOL_MAPPERS:
                try:
                    keycloak_admin.add_mapper_to_client(client_uuid, mapper)
                    print(f"   ✅ Mapper adicionado: {mapper['name']}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"   ⚠️  Mapper já existe: {mapper['name']}")
                    else:
                        print(f"   ❌ Erro ao adicionar mapper {mapper['name']}: {e}")

        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ⚠️  Client já existe: {client_id}")
                # Tentar obter secret do client existente
                try:
                    clients = keycloak_admin.get_clients()
                    for c in clients:
                        if c.get("clientId") == client_id:
                            client_uuid = c.get("id")
                            client_secret = keycloak_admin.get_client_secrets(client_uuid)
                            secret = client_secret.get("value")
                            client_secrets[client_id] = secret
                            print(f"   🔑 Secret obtido: {secret[:20]}...")
                            break
                except Exception as e2:
                    print(f"   ❌ Erro ao obter secret: {e2}")
            else:
                print(f"   ❌ Erro ao criar client: {e}")

    # Salvar secrets em arquivo
    print(f"\n💾 Salvando Client Secrets...")
    print("-" * 60)

    secrets_file = "keycloak_client_secrets.json"
    with open(secrets_file, "w") as f:
        json.dump(client_secrets, f, indent=2)

    print(f"✅ Secrets salvos em: {secrets_file}")
    print(f"⚠️  IMPORTANTE: Guarde este arquivo com segurança!")

    # Criar arquivo .env de exemplo
    env_example = "# IntelliCare Keycloak Configuration\n"
    env_example += "# Gerado automaticamente pelo setup_keycloak.py\n\n"
    env_example += f"KEYCLOAK_SERVER_URL={KEYCLOAK_URL}\n"
    env_example += f"KEYCLOAK_REALM={REALM_NAME}\n\n"

    for client_id, secret in client_secrets.items():
        env_example += f"# {client_id}\n"
        env_example += f"# KEYCLOAK_CLIENT_ID={client_id}\n"
        env_example += f"# KEYCLOAK_CLIENT_SECRET={secret}\n\n"

    with open(".env.example", "w") as f:
        f.write(env_example)

    print(f"✅ Exemplo .env criado: .env.example")

    # Resumo
    print(f"\n" + "=" * 60)
    print(f"✅ SETUP CONCLUÍDO COM SUCESSO!")
    print(f"=" * 60)
    print(f"\n📊 Resumo:")
    print(f"   - Roles criadas: {len(created_roles)}")
    print(f"   - Clients criados: {len(client_secrets)}")
    print(f"   - Protocol mappers: {len(PROTOCOL_MAPPERS)} por client")

    print(f"\n📝 Próximos passos:")
    print(f"   1. Revisar secrets em: {secrets_file}")
    print(f"   2. Criar usuários de teste no Keycloak")
    print(f"   3. Testar autenticação com: python examples/test_connection.py")
    print(f"   4. Integrar módulos usando: docs/GUIA_INTEGRACAO.md")

    print(f"\n🔗 Keycloak Admin Console:")
    print(f"   {KEYCLOAK_URL}admin/")
    print(f"   Realm: {REALM_NAME}")


if __name__ == "__main__":
    setup_keycloak()


