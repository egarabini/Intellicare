#!/usr/bin/env python3
"""
Teste simples de integração Keycloak para intellicare-geralda
Não requer servidor rodando
"""

import httpx
import sys

KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-geralda"
CLIENT_SECRET = "kihZ6pvwObfdg3UPoc1wUklbQmQp1PpB"
TEST_USER = "dr.silva@saudeplanner.com.br"
TEST_PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print(f"🧪 TESTE SIMPLES - INTEGRAÇÃO KEYCLOAK - INTELLICARE-GERALDA")
    print("=" * 80)
    print()
    
    passed = 0
    total = 4
    
    # TESTE 1: Keycloak acessível
    print("TESTE 1: Verificando se Keycloak está acessível...")
    print("-" * 80)
    try:
        response = httpx.get(f"{KEYCLOAK_URL}/realms/{REALM}", verify=False, timeout=10)
        if response.status_code == 200:
            print("✅ PASSOU: Keycloak está acessível")
            print(f"   URL: {KEYCLOAK_URL}")
            print(f"   Realm: {REALM}")
            print(f"   Status: {response.status_code}")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FALHOU: {e}")
    print()
    
    # TESTE 2: Token com usuário
    print("TESTE 2: Obtendo token com usuário válido...")
    print("-" * 80)
    try:
        token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": TEST_USER,
            "password": TEST_PASSWORD
        }
        
        response = httpx.post(token_url, data=data, verify=False, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ PASSOU: Token obtido com sucesso")
            print(f"   Usuário: {TEST_USER}")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Expires In: {token_data.get('expires_in')} segundos")
            print(f"   Token (primeiros 50 chars): {token_data.get('access_token', '')[:50]}...")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ FALHOU: {e}")
    print()
    
    # TESTE 3: Credenciais inválidas
    print("TESTE 3: Verificando rejeição de credenciais inválidas...")
    print("-" * 80)
    try:
        response = httpx.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "username": "invalid@user.com",
                "password": "wrongpassword"
            },
            verify=False,
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ PASSOU: Credenciais inválidas foram rejeitadas")
            print(f"   Status: {response.status_code} (Unauthorized)")
            passed += 1
        else:
            print(f"❌ FALHOU: Esperado 401, recebido {response.status_code}")
    except Exception as e:
        print(f"❌ FALHOU: {e}")
    print()
    
    # TESTE 4: Client credentials
    print("TESTE 4: Verificando configuração do cliente...")
    print("-" * 80)
    try:
        response = httpx.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            },
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ PASSOU: Cliente configurado corretamente")
            print(f"   Client ID: {CLIENT_ID}")
            print(f"   Status: {response.status_code}")
            print("   Client Credentials: Habilitado")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ FALHOU: {e}")
    print()
    
    # Resumo
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    print(f"✅ Testes que passaram: {passed}")
    print(f"❌ Testes que falharam: {total - passed}")
    print(f"📈 Total de testes: {total}")
    print()
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print()
        print("✅ Keycloak está configurado corretamente")
        print("✅ Autenticação está funcionando")
        print(f"✅ Cliente {CLIENT_ID} está OK")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        sys.exit(1)

if __name__ == "__main__":
    main()
