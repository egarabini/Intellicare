#!/usr/bin/env python3
"""
Script para verificar os client secrets de todos os clientes IntelliCare
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import urllib3
import json

# Desabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"

# Todos os clientes IntelliCare
CLIENTS = [
    "intellicare-core",
    "intellicare-wanda",
    "intellicare-florence",
    "intellicare-oswaldo",
    "intellicare-zilda",
    "intellicare-geralda",
    "intellicare-donabedian",
    "intellicare-comunicacao",
    "intellicare-portal"
]

def main():
    print("=" * 80)
    print("🔍 VERIFICANDO CLIENT SECRETS")
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
        
        # Carregar secrets do arquivo JSON
        secrets_file = Path(__file__).parent.parent / "keycloak_client_secrets.json"
        
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                saved_secrets = json.load(f)
            print("📂 Secrets salvos carregados")
            print()
        else:
            saved_secrets = {}
            print("⚠️  Arquivo de secrets não encontrado")
            print()
        
        current_secrets = {}
        
        # 2. Para cada cliente
        for client_id in CLIENTS:
            print(f"🔍 Verificando: {client_id}")
            
            # Buscar cliente
            clients_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/clients?clientId={client_id}"
            clients_response = requests.get(clients_url, headers=headers, verify=False)
            
            if clients_response.status_code != 200:
                print(f"   ❌ Erro ao buscar cliente: {clients_response.status_code}")
                print()
                continue
            
            clients = clients_response.json()
            
            if not clients:
                print(f"   ❌ Cliente não encontrado")
                print()
                continue
            
            client = clients[0]
            client_uuid = client["id"]
            
            # Buscar secret
            secret_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/clients/{client_uuid}/client-secret"
            secret_response = requests.get(secret_url, headers=headers, verify=False)
            
            if secret_response.status_code == 200:
                current_secret = secret_response.json().get("value")
                current_secrets[client_id] = current_secret
                
                saved_secret = saved_secrets.get(client_id, "N/A")
                
                if current_secret == saved_secret:
                    print(f"   ✅ Secret CORRETO: {current_secret[:10]}...")
                else:
                    print(f"   ⚠️  Secret DIFERENTE!")
                    print(f"      Keycloak: {current_secret[:10]}...")
                    print(f"      Salvo:    {saved_secret[:10] if saved_secret != 'N/A' else 'N/A'}...")
            else:
                print(f"   ❌ Erro ao buscar secret: {secret_response.status_code}")
            
            print()
        
        # Salvar secrets atuais
        print("=" * 80)
        print("💾 SALVANDO SECRETS ATUAIS")
        print("=" * 80)
        print()
        
        with open(secrets_file, 'w') as f:
            json.dump(current_secrets, f, indent=2)
        
        print(f"✅ Secrets salvos em: {secrets_file}")
        print()
        
        # Mostrar secrets
        print("=" * 80)
        print("📋 SECRETS ATUAIS")
        print("=" * 80)
        print()
        
        for client_id, secret in current_secrets.items():
            print(f"{client_id}: {secret}")
        
        print()
        print("🎉 VERIFICAÇÃO CONCLUÍDA!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

