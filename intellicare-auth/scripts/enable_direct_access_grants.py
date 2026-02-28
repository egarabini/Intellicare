#!/usr/bin/env python3
"""
Script para habilitar Direct Access Grants no cliente intellicare-donabedian
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin

KEYCLOAK_URL = "https://keycloak.gsi.srv.br/"
ADMIN_USERNAME = "egarabini@gmail.com"
ADMIN_PASSWORD = "Crazy#57LB"
REALM_NAME = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"

def main():
    print("=" * 80)
    print("🔧 HABILITANDO DIRECT ACCESS GRANTS")
    print("=" * 80)
    print()
    
    try:
        # Conectar
        print(f"📡 Conectando ao Keycloak...")
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USERNAME,
            password=ADMIN_PASSWORD,
            realm_name="master",
            verify=False
        )
        keycloak_admin.realm_name = REALM_NAME
        print("✅ Conectado!")
        print()
        
        # Buscar cliente
        print(f"🔍 Buscando cliente: {CLIENT_ID}")
        client_id_keycloak = keycloak_admin.get_client_id(CLIENT_ID)
        
        if not client_id_keycloak:
            print(f"❌ Cliente não encontrado!")
            sys.exit(1)
        
        print(f"✅ Cliente encontrado! ID: {client_id_keycloak}")
        print()
        
        # Buscar configuração atual
        print("📋 Configuração atual:")
        client = keycloak_admin.get_client(client_id_keycloak)
        
        print(f"   Client ID: {client.get('clientId')}")
        print(f"   Enabled: {client.get('enabled')}")
        print(f"   Direct Access Grants: {client.get('directAccessGrantsEnabled')}")
        print(f"   Standard Flow: {client.get('standardFlowEnabled')}")
        print(f"   Service Accounts: {client.get('serviceAccountsEnabled')}")
        print()
        
        # Atualizar configuração
        print("🔧 Habilitando Direct Access Grants...")
        
        keycloak_admin.update_client(
            client_id_keycloak,
            {
                "directAccessGrantsEnabled": True,
                "standardFlowEnabled": True,
                "serviceAccountsEnabled": True,
                "publicClient": False,
                "protocol": "openid-connect"
            }
        )
        
        print("✅ Configuração atualizada!")
        print()
        
        # Verificar nova configuração
        print("📋 Nova configuração:")
        client = keycloak_admin.get_client(client_id_keycloak)
        
        print(f"   Direct Access Grants: {client.get('directAccessGrantsEnabled')}")
        print(f"   Standard Flow: {client.get('standardFlowEnabled')}")
        print(f"   Service Accounts: {client.get('serviceAccountsEnabled')}")
        print()
        
        print("=" * 80)
        print("🎉 CONCLUÍDO!")
        print("=" * 80)
        print()
        print("O cliente agora suporta:")
        print("  ✅ Direct Access Grants (Password Flow)")
        print("  ✅ Standard Flow (Authorization Code)")
        print("  ✅ Service Accounts (Client Credentials)")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

