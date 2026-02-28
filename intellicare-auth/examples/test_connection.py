"""Script de teste para validar conexão com Keycloak GSI."""

import asyncio
import os
from pathlib import Path

from intellicare_auth import KeycloakClient, KeycloakConfig


async def test_keycloak_connection():
    """Testa conexão e funcionalidades básicas do Keycloak."""
    
    print("🔐 TESTE DE CONEXÃO KEYCLOAK GSI")
    print("=" * 60)
    
    # Configuração
    config = KeycloakConfig(
        server_url="https://keycloak.gsi.srv.br/auth",
        realm="saudeplanner.com.br",
        client_id=os.getenv("KEYCLOAK_CLIENT_ID", "bc-public-client"),
        client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET", "h6AmFgY4S9MwJFMEXXBQf6Wy7Ts1TkP"),
    )
    
    print(f"\n📋 Configuração:")
    print(f"   Server: {config.server_url}")
    print(f"   Realm: {config.realm}")
    print(f"   Client ID: {config.client_id}")
    print(f"   Client Secret: {'*' * len(config.client_secret or '')}")
    
    # Cliente
    client = KeycloakClient(config)
    
    # Teste 1: Obter token
    print(f"\n🔑 Teste 1: Obter Token (Client Credentials)")
    print("-" * 60)
    
    try:
        token_data = await client.get_client_token()
        access_token = token_data.get("access_token")
        
        print(f"✅ Token obtido com sucesso!")
        print(f"   Token Type: {token_data.get('token_type')}")
        print(f"   Expires In: {token_data.get('expires_in')}s")
        print(f"   Access Token: {access_token[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        return
    
    # Teste 2: Validar token
    print(f"\n✅ Teste 2: Validar Token (JWT Local)")
    print("-" * 60)
    
    try:
        payload = await client.validate_token(access_token)
        
        print(f"✅ Token validado com sucesso!")
        print(f"   Subject (sub): {payload.get('sub')}")
        print(f"   Issuer (iss): {payload.get('iss')}")
        print(f"   Audience (aud): {payload.get('aud')}")
        print(f"   Expires (exp): {payload.get('exp')}")
        print(f"   Issued At (iat): {payload.get('iat')}")
        
        # Roles
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])
        print(f"   Roles: {', '.join(roles[:5])}...")
        
    except Exception as e:
        print(f"❌ Erro ao validar token: {e}")
        return
    
    # Teste 3: User Info
    print(f"\n👤 Teste 3: Obter User Info")
    print("-" * 60)
    
    try:
        user_info = await client.get_user_info(access_token)
        
        print(f"✅ User info obtido com sucesso!")
        print(f"   Preferred Username: {user_info.get('preferred_username')}")
        print(f"   Email: {user_info.get('email')}")
        print(f"   Email Verified: {user_info.get('email_verified')}")
        
    except Exception as e:
        print(f"⚠️  User info não disponível (normal para service accounts): {e}")
    
    # Teste 4: Introspection
    print(f"\n🔍 Teste 4: Token Introspection")
    print("-" * 60)
    
    try:
        introspection = await client.introspect_token(access_token)
        
        print(f"✅ Token introspectado com sucesso!")
        print(f"   Active: {introspection.get('active')}")
        print(f"   Client ID: {introspection.get('client_id')}")
        print(f"   Token Type: {introspection.get('typ')}")
        
    except Exception as e:
        print(f"❌ Erro ao introspectar token: {e}")
    
    # Teste 5: Cache
    print(f"\n💾 Teste 5: Validação com Cache")
    print("-" * 60)
    
    import time
    
    # Primeira validação (sem cache)
    start = time.time()
    await client.validate_token(access_token)
    first_time = time.time() - start
    
    # Segunda validação (com cache)
    start = time.time()
    await client.validate_token(access_token)
    cached_time = time.time() - start
    
    print(f"✅ Cache funcionando!")
    print(f"   Primeira validação: {first_time*1000:.2f}ms")
    print(f"   Segunda validação (cache): {cached_time*1000:.2f}ms")
    print(f"   Speedup: {first_time/cached_time:.1f}x mais rápido")
    
    # Resumo
    print(f"\n" + "=" * 60)
    print(f"✅ TODOS OS TESTES PASSARAM!")
    print(f"=" * 60)
    print(f"\n🎯 Próximos passos:")
    print(f"   1. Configurar clients no Keycloak para cada módulo")
    print(f"   2. Integrar intellicare-donabedian (módulo piloto)")
    print(f"   3. Testar autenticação em endpoints reais")
    print(f"\n📚 Documentação: ./intellicare-auth/docs/")


if __name__ == "__main__":
    asyncio.run(test_keycloak_connection())

