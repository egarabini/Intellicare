#!/usr/bin/env python3
"""
Script para habilitar Direct Access Grants em TODOS os clientes IntelliCare
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
    print("🔧 HABILITANDO DIRECT ACCESS GRANTS EM TODOS OS CLIENTES")
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
        
        success_count = 0
        failed_count = 0
        
        # 2. Para cada cliente
        for client_id in CLIENTS:
            print(f"🔧 Processando: {client_id}")
            
            # Buscar cliente
            clients_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/clients?clientId={client_id}"
            clients_response = requests.get(clients_url, headers=headers, verify=False)
            
            if clients_response.status_code != 200:
                print(f"   ❌ Erro ao buscar cliente: {clients_response.status_code}")
                failed_count += 1
                print()
                continue
            
            clients = clients_response.json()
            
            if not clients:
                print(f"   ❌ Cliente não encontrado")
                failed_count += 1
                print()
                continue
            
            client = clients[0]
            client_uuid = client["id"]
            
            # Verificar se já está habilitado
            if client.get("directAccessGrantsEnabled"):
                print(f"   ✅ Direct Access Grants já habilitado")
                success_count += 1
                print()
                continue
            
            # Atualizar cliente
            update_url = f"{KEYCLOAK_URL}admin/realms/{REALM_NAME}/clients/{client_uuid}"
            
            # Manter todas as configurações existentes e apenas habilitar Direct Access Grants
            client["directAccessGrantsEnabled"] = True
            
            update_response = requests.put(
                update_url,
                json=client,
                headers=headers,
                verify=False
            )
            
            if update_response.status_code == 204:
                print(f"   ✅ Direct Access Grants HABILITADO")
                success_count += 1
            else:
                print(f"   ❌ Erro ao atualizar: {update_response.status_code}")
                print(f"      Response: {update_response.text}")
                failed_count += 1
            
            print()
        
        # Resumo
        print("=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        print(f"✅ Clientes configurados: {success_count}")
        print(f"❌ Clientes com erro: {failed_count}")
        print(f"📈 Total processado: {len(CLIENTS)}")
        print()
        
        if success_count == len(CLIENTS):
            print("🎉 TODOS OS CLIENTES CONFIGURADOS COM SUCESSO!")
            print()
            print("✅ Direct Access Grants habilitado em todos os clientes")
            print("✅ Agora você pode usar password grant flow")
            print("✅ Testes devem passar")
            sys.exit(0)
        else:
            print("⚠️  ALGUNS CLIENTES FALHARAM")
            print()
            print("Verifique os erros acima.")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

