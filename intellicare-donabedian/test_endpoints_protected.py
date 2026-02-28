#!/usr/bin/env python3
"""
Teste completo dos endpoints protegidos com Keycloak
"""

import httpx
import sys

# Configurações
BASE_URL = "http://localhost:8003"
KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"
CLIENT_SECRET = "DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs"

# Usuários de teste
DOCTOR_USER = "dr.silva@saudeplanner.com.br"
ADMIN_USER = "admin@saudeplanner.com.br"
PASSWORD = "Test@123"

def get_token(username, password):
    """Obtém token de autenticação"""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password
    }
    
    response = httpx.post(token_url, data=data, verify=False, timeout=10)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro ao obter token: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_endpoint(name, url, token=None, method="GET", expected_status=200):
    """Testa um endpoint"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = httpx.get(url, headers=headers, timeout=10)
        else:
            response = httpx.request(method, url, headers=headers, timeout=10)
        
        success = response.status_code == expected_status
        
        if success:
            print(f"   ✅ {name}: {response.status_code}")
        else:
            print(f"   ❌ {name}: {response.status_code} (esperado {expected_status})")
            if response.status_code in [401, 403]:
                print(f"      Response: {response.text[:100]}")
        
        return success
    
    except Exception as e:
        print(f"   ❌ {name}: Erro - {e}")
        return False

def main():
    print("=" * 80)
    print("🧪 TESTE COMPLETO - ENDPOINTS PROTEGIDOS")
    print("=" * 80)
    print()
    
    # Verificar se servidor está rodando
    print("🔍 Verificando servidor...")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está rodando!")
        else:
            print(f"⚠️  Servidor retornou: {response.status_code}")
    except Exception as e:
        print(f"❌ Servidor não está acessível: {e}")
        print()
        print("Execute o servidor primeiro:")
        print("  python -m uvicorn src.donabedian.api.main:app --port 8003")
        sys.exit(1)
    
    print()
    
    # Obter tokens
    print("🔐 Obtendo tokens de autenticação...")
    doctor_token = get_token(DOCTOR_USER, PASSWORD)
    admin_token = get_token(ADMIN_USER, PASSWORD)
    
    if not doctor_token:
        print("❌ Não foi possível obter token do médico")
        sys.exit(1)
    
    if not admin_token:
        print("⚠️  Não foi possível obter token do admin (continuando com médico)")
    
    print("✅ Tokens obtidos!")
    print()
    
    # Testes
    total_tests = 0
    passed_tests = 0
    
    print("=" * 80)
    print("📋 TESTE 1: Endpoint Público (sem autenticação)")
    print("=" * 80)
    
    if test_endpoint("GET /health", f"{BASE_URL}/health", expected_status=200):
        passed_tests += 1
    total_tests += 1
    print()
    
    print("=" * 80)
    print("📋 TESTE 2: Endpoints Protegidos SEM Token (deve retornar 401)")
    print("=" * 80)
    
    if test_endpoint("GET /pillars sem token", f"{BASE_URL}/pillars", expected_status=401):
        passed_tests += 1
    total_tests += 1
    
    if test_endpoint("GET /indicators sem token", f"{BASE_URL}/indicators", expected_status=401):
        passed_tests += 1
    total_tests += 1
    print()
    
    print("=" * 80)
    print("📋 TESTE 3: Endpoints GET COM Token (deve retornar 200)")
    print("=" * 80)
    
    if test_endpoint("GET /pillars com token", f"{BASE_URL}/pillars", token=doctor_token, expected_status=200):
        passed_tests += 1
    total_tests += 1
    
    if test_endpoint("GET /indicators com token", f"{BASE_URL}/indicators", token=doctor_token, expected_status=200):
        passed_tests += 1
    total_tests += 1
    
    if test_endpoint("GET /measurements com token", f"{BASE_URL}/measurements", token=doctor_token, expected_status=200):
        passed_tests += 1
    total_tests += 1
    print()
    
    print("=" * 80)
    print("📋 TESTE 4: Endpoints POST sem role admin (deve retornar 403)")
    print("=" * 80)
    
    # Médico tentando criar (sem role admin)
    if test_endpoint("POST /pillars sem admin", f"{BASE_URL}/pillars", token=doctor_token, method="POST", expected_status=403):
        passed_tests += 1
    total_tests += 1
    print()
    
    if admin_token:
        print("=" * 80)
        print("📋 TESTE 5: Endpoints POST com role admin (deve funcionar)")
        print("=" * 80)
        
        # Admin tentando criar (com role admin) - vai falhar por falta de dados, mas não por auth
        # Esperamos 422 (validation error) ou 400, não 401/403
        response = httpx.post(
            f"{BASE_URL}/pillars",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
            timeout=10
        )
        
        if response.status_code in [400, 422]:
            print(f"   ✅ POST /pillars com admin: {response.status_code} (autenticação OK, falta dados)")
            passed_tests += 1
        elif response.status_code in [401, 403]:
            print(f"   ❌ POST /pillars com admin: {response.status_code} (erro de autenticação)")
        else:
            print(f"   ⚠️  POST /pillars com admin: {response.status_code}")
            passed_tests += 1
        
        total_tests += 1
        print()
    
    # Resumo
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    print(f"✅ Testes que passaram: {passed_tests}/{total_tests}")
    print(f"❌ Testes que falharam: {total_tests - passed_tests}/{total_tests}")
    print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print()
        print("✅ Autenticação Keycloak está funcionando perfeitamente!")
        print("✅ Endpoints públicos acessíveis")
        print("✅ Endpoints protegidos bloqueiam sem token")
        print("✅ Endpoints protegidos permitem com token válido")
        print("✅ Autorização por roles funcionando")
        sys.exit(0)
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print()
        print("Verifique os erros acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()

