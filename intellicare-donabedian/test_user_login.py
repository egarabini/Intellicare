#!/usr/bin/env python3
"""
Teste direto de login do usuário
"""

import httpx
import json

KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"
CLIENT_SECRET = "DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs"

print("=" * 80)
print("🧪 TESTE DE LOGIN DIRETO")
print("=" * 80)
print()

# Testar com diferentes usuários
test_users = [
    ("dr.silva@saudeplanner.com.br", "Test@123"),
    ("admin@saudeplanner.com.br", "Test@123"),
]

token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

for username, password in test_users:
    print(f"👤 Testando: {username}")
    print(f"   Senha: {password}")
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password,
        "scope": "openid profile email"
    }
    
    try:
        response = httpx.post(token_url, data=data, verify=False, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ SUCESSO!")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Expires In: {token_data.get('expires_in')} segundos")
            print(f"   Access Token (50 chars): {token_data.get('access_token', '')[:50]}...")
        else:
            print(f"   ❌ FALHOU")
            print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print()

print("=" * 80)
print("🔍 DIAGNÓSTICO")
print("=" * 80)
print()
print("Se todos falharam com 'Invalid user credentials', pode ser:")
print("  1. Usuário não existe no realm bemcuidar")
print("  2. Senha está incorreta")
print("  3. Usuário está desabilitado")
print("  4. Email não foi verificado (se requerido)")
print()

