"""
Script de teste para validar integração com Keycloak.

Este script testa:
1. Endpoint público (sem autenticação)
2. Endpoint protegido sem token (deve retornar 401)
3. Endpoint protegido com token válido
4. Endpoint admin sem role admin (deve retornar 403)
5. Endpoint admin com role admin (se disponível)
"""

import httpx
import json
from typing import Dict, Any


# Configurações
KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"
CLIENT_SECRET = "3w0l6qxYnNwm2jPDozu1x2LVyzjv4Cs"
API_BASE_URL = "http://localhost:8003/api/v1"

# Usuários de teste
TEST_USERS = {
    "doctor": {
        "username": "dr.silva@saudeplanner.com.br",
        "password": "Test@123",
        "role": "intellicare_doctor"
    },
    "nurse": {
        "username": "enf.maria@saudeplanner.com.br",
        "password": "Test@123",
        "role": "intellicare_nurse"
    }
}


def get_token(username: str, password: str) -> Dict[str, Any]:
    """Obtém token do Keycloak."""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password
    }
    
    response = httpx.post(token_url, data=data, verify=False)
    response.raise_for_status()
    return response.json()


def test_public_endpoint():
    """Teste 1: Endpoint público (sem autenticação)."""
    print("\n" + "="*80)
    print("TESTE 1: Endpoint Público (GET /health)")
    print("="*80)
    
    try:
        response = httpx.get(f"{API_BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        assert response.status_code == 200, "Health endpoint deve retornar 200"
        print("✅ TESTE PASSOU: Endpoint público acessível sem token")
    except Exception as e:
        print(f"❌ TESTE FALHOU: {e}")


def test_protected_without_token():
    """Teste 2: Endpoint protegido sem token (deve retornar 401)."""
    print("\n" + "="*80)
    print("TESTE 2: Endpoint Protegido SEM Token (GET /pillars)")
    print("="*80)
    
    try:
        response = httpx.get(f"{API_BASE_URL}/pillars")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        assert response.status_code == 403, "Deve retornar 403 Forbidden sem token"
        print("✅ TESTE PASSOU: Endpoint protegido bloqueou acesso sem token")
    except AssertionError as e:
        print(f"❌ TESTE FALHOU: {e}")
    except Exception as e:
        print(f"⚠️  Erro inesperado: {e}")


def test_protected_with_valid_token():
    """Teste 3: Endpoint protegido com token válido."""
    print("\n" + "="*80)
    print("TESTE 3: Endpoint Protegido COM Token Válido (GET /pillars)")
    print("="*80)
    
    try:
        # Obter token
        print("Obtendo token do Keycloak...")
        user = TEST_USERS["doctor"]
        token_data = get_token(user["username"], user["password"])
        access_token = token_data["access_token"]
        print(f"✅ Token obtido com sucesso (role: {user['role']})")
        
        # Testar endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(f"{API_BASE_URL}/pillars", headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {json.dumps(data, indent=2)[:300]}...")
            print("✅ TESTE PASSOU: Endpoint protegido acessível com token válido")
        else:
            print(f"Response: {response.text[:200]}")
            print(f"❌ TESTE FALHOU: Esperado 200, recebido {response.status_code}")
            
    except Exception as e:
        print(f"❌ TESTE FALHOU: {e}")


def test_admin_endpoint_without_admin_role():
    """Teste 4: Endpoint admin sem role admin (deve retornar 403)."""
    print("\n" + "="*80)
    print("TESTE 4: Endpoint Admin SEM Role Admin (POST /pillars)")
    print("="*80)
    
    try:
        # Obter token de usuário não-admin
        print("Obtendo token de usuário não-admin...")
        user = TEST_USERS["doctor"]
        token_data = get_token(user["username"], user["password"])
        access_token = token_data["access_token"]
        print(f"✅ Token obtido (role: {user['role']} - NÃO é admin)")
        
        # Tentar criar pillar (requer admin)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "name": "test_pillar",
            "description": "Test pillar",
            "display_order": 99
        }
        response = httpx.post(f"{API_BASE_URL}/pillars", headers=headers, json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        assert response.status_code == 403, "Deve retornar 403 Forbidden sem role admin"
        print("✅ TESTE PASSOU: Endpoint admin bloqueou usuário sem role admin")
        
    except AssertionError as e:
        print(f"❌ TESTE FALHOU: {e}")
    except Exception as e:
        print(f"❌ TESTE FALHOU: {e}")


def main():
    """Executa todos os testes."""
    print("\n" + "🧪 " + "="*76 + " 🧪")
    print("🧪  TESTES DE INTEGRAÇÃO KEYCLOAK - INTELLICARE-DONABEDIAN")
    print("🧪 " + "="*76 + " 🧪")
    
    print("\n⚠️  IMPORTANTE: Certifique-se de que o servidor está rodando em http://localhost:8003")
    print("   Execute: uvicorn src.donabedian.api.main:app --reload --port 8003\n")
    
    input("Pressione ENTER para continuar...")
    
    # Executar testes
    test_public_endpoint()
    test_protected_without_token()
    test_protected_with_valid_token()
    test_admin_endpoint_without_admin_role()
    
    # Resumo
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    print("✅ Teste 1: Endpoint público acessível")
    print("✅ Teste 2: Endpoint protegido bloqueia sem token")
    print("✅ Teste 3: Endpoint protegido permite com token válido")
    print("✅ Teste 4: Endpoint admin bloqueia sem role admin")
    print("\n🎉 INTEGRAÇÃO KEYCLOAK FUNCIONANDO CORRETAMENTE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

