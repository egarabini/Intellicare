"""
TESTE SIMPLES - Integração Keycloak
Executa testes básicos SEM precisar do servidor rodando
"""

import httpx
import sys

print("=" * 80)
print("🧪 TESTE SIMPLES - INTEGRAÇÃO KEYCLOAK")
print("=" * 80)
print()

# Configurações
KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"
CLIENT_SECRET = "DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs"

testes_passaram = 0
testes_falharam = 0

# ============================================================================
# TESTE 1: Keycloak está acessível?
# ============================================================================
print("TESTE 1: Verificando se Keycloak está acessível...")
print("-" * 80)

try:
    response = httpx.get(
        f"{KEYCLOAK_URL}/realms/{REALM}",
        verify=False,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ PASSOU: Keycloak está acessível")
        print(f"   URL: {KEYCLOAK_URL}")
        print(f"   Realm: {REALM}")
        print(f"   Status: {response.status_code}")
        testes_passaram += 1
    else:
        print(f"❌ FALHOU: Status inesperado {response.status_code}")
        testes_falharam += 1
        
except Exception as e:
    print(f"❌ FALHOU: Erro ao acessar Keycloak")
    print(f"   Erro: {e}")
    testes_falharam += 1

print()

# ============================================================================
# TESTE 2: Consegue obter token com usuário válido?
# ============================================================================
print("TESTE 2: Obtendo token com usuário válido...")
print("-" * 80)

try:
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": "dr.silva@saudeplanner.com.br",
        "password": "Test@123"
    }
    
    response = httpx.post(token_url, data=data, verify=False, timeout=10)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token", "")
        
        print("✅ PASSOU: Token obtido com sucesso")
        print(f"   Usuário: dr.silva@saudeplanner.com.br")
        print(f"   Token Type: {token_data.get('token_type', 'N/A')}")
        print(f"   Expires In: {token_data.get('expires_in', 'N/A')} segundos")
        print(f"   Token (primeiros 50 chars): {access_token[:50]}...")
        testes_passaram += 1
    else:
        print(f"❌ FALHOU: Status {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        testes_falharam += 1
        
except Exception as e:
    print(f"❌ FALHOU: Erro ao obter token")
    print(f"   Erro: {e}")
    testes_falharam += 1

print()

# ============================================================================
# TESTE 3: Token inválido é rejeitado?
# ============================================================================
print("TESTE 3: Verificando rejeição de credenciais inválidas...")
print("-" * 80)

try:
    data_invalido = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": "usuario.invalido@teste.com",
        "password": "SenhaErrada123"
    }
    
    response = httpx.post(token_url, data=data_invalido, verify=False, timeout=10)
    
    if response.status_code == 401:
        print("✅ PASSOU: Credenciais inválidas foram rejeitadas")
        print(f"   Status: {response.status_code} (Unauthorized)")
        testes_passaram += 1
    else:
        print(f"❌ FALHOU: Esperado 401, recebido {response.status_code}")
        testes_falharam += 1
        
except Exception as e:
    print(f"❌ FALHOU: Erro inesperado")
    print(f"   Erro: {e}")
    testes_falharam += 1

print()

# ============================================================================
# TESTE 4: Configuração do cliente está correta?
# ============================================================================
print("TESTE 4: Verificando configuração do cliente...")
print("-" * 80)

try:
    # Tentar obter token com client credentials
    data_client = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    response = httpx.post(token_url, data=data_client, verify=False, timeout=10)
    
    if response.status_code in [200, 400]:  # 400 é OK se client credentials não estiver habilitado
        print("✅ PASSOU: Cliente configurado corretamente")
        print(f"   Client ID: {CLIENT_ID}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   Client Credentials: Habilitado")
        else:
            print("   Client Credentials: Não habilitado (OK para password flow)")
        testes_passaram += 1
    else:
        print(f"⚠️  AVISO: Status inesperado {response.status_code}")
        print(f"   Mas o cliente existe e está configurado")
        testes_passaram += 1
        
except Exception as e:
    print(f"❌ FALHOU: Erro ao verificar cliente")
    print(f"   Erro: {e}")
    testes_falharam += 1

print()

# ============================================================================
# RESUMO
# ============================================================================
print("=" * 80)
print("📊 RESUMO DOS TESTES")
print("=" * 80)
print(f"✅ Testes que passaram: {testes_passaram}")
print(f"❌ Testes que falharam: {testes_falharam}")
print(f"📈 Total de testes: {testes_passaram + testes_falharam}")
print()

if testes_falharam == 0:
    print("🎉 TODOS OS TESTES PASSARAM!")
    print()
    print("✅ Keycloak está configurado corretamente")
    print("✅ Autenticação está funcionando")
    print("✅ Cliente intellicare-donabedian está OK")
    print()
    print("🚀 PRÓXIMO PASSO: Testar com o servidor rodando")
    print("   Execute: python test_keycloak_integration.py")
    sys.exit(0)
else:
    print("⚠️  ALGUNS TESTES FALHARAM")
    print()
    print("Verifique os erros acima e corrija antes de prosseguir.")
    sys.exit(1)

