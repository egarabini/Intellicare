"""Teste rápido de autenticação Keycloak"""
import httpx

KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "intellicare-donabedian"
CLIENT_SECRET = "3w0l6qxYnNwm2jPDozu1x2LVyzjv4Cs"

print("🧪 Testando autenticação Keycloak...")
print(f"   Server: {KEYCLOAK_URL}")
print(f"   Realm: {REALM}")
print(f"   Client: {CLIENT_ID}")
print()

# Obter token
token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

data = {
    "grant_type": "password",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "username": "dr.silva@saudeplanner.com.br",
    "password": "Test@123"
}

try:
    response = httpx.post(token_url, data=data, verify=False, timeout=10)
    response.raise_for_status()
    token_data = response.json()
    
    print("✅ Token obtido com sucesso!")
    print(f"   Access Token: {token_data['access_token'][:50]}...")
    print(f"   Token Type: {token_data['token_type']}")
    print(f"   Expires In: {token_data['expires_in']} segundos")
    print()
    print("🎉 AUTENTICAÇÃO KEYCLOAK FUNCIONANDO!")
    
except Exception as e:
    print(f"❌ Erro ao obter token: {e}")

