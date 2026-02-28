#!/usr/bin/env python3
"""
Script para replicar configuração Keycloak para um módulo IntelliCare
Usa intellicare-donabedian como template
"""

import sys
import os
from pathlib import Path
import shutil
import json

# Mapeamento de módulos
MODULES = {
    "intellicare-core": {
        "port": 8000,
        "client_id": "intellicare-core",
        "package_name": "intellicare_core",
        "main_module": "core"
    },
    "intellicare-wanda": {
        "port": 8007,
        "client_id": "intellicare-wanda",
        "package_name": "intellicare_wanda",
        "main_module": "wanda"
    },
    "intellicare-florence": {
        "port": 8001,
        "client_id": "intellicare-florence",
        "package_name": "intellicare_florence",
        "main_module": "florence"
    },
    "intellicare-oswaldo": {
        "port": 8002,
        "client_id": "intellicare-oswaldo",
        "package_name": "intellicare_oswaldo",
        "main_module": "oswaldo"
    },
    "intellicare-zilda": {
        "port": 8004,
        "client_id": "intellicare-zilda",
        "package_name": "intellicare_zilda",
        "main_module": "zilda"
    },
    "intellicare-geralda": {
        "port": 8005,
        "client_id": "intellicare-geralda",
        "package_name": "intellicare_geralda",
        "main_module": "geralda"
    },
    "intellicare-comunicacao": {
        "port": 8011,
        "client_id": "intellicare-comunicacao",
        "package_name": "intellicare_comunicacao",
        "main_module": "comunicacao"
    }
}

def load_client_secrets():
    """Carrega os client secrets do arquivo JSON"""
    secrets_file = Path(__file__).parent.parent / "keycloak_client_secrets.json"
    
    if not secrets_file.exists():
        print(f"❌ Arquivo de secrets não encontrado: {secrets_file}")
        sys.exit(1)
    
    with open(secrets_file, 'r') as f:
        return json.load(f)

def create_env_keycloak(module_name, module_info, client_secret):
    """Cria arquivo .env.keycloak para o módulo"""
    
    env_content = f"""# Keycloak Configuration for {module_name}
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/
KEYCLOAK_REALM=bemcuidar
KEYCLOAK_CLIENT_ID={module_info['client_id']}
KEYCLOAK_CLIENT_SECRET={client_secret}

# Cache settings
KEYCLOAK_JWKS_CACHE_TTL=300
KEYCLOAK_TOKEN_CACHE_TTL=60

# Validation settings
KEYCLOAK_VERIFY_SSL=true
KEYCLOAK_VALIDATE_AUDIENCE=true
KEYCLOAK_VALIDATE_ISSUER=true
"""
    
    return env_content

def create_test_simple(module_name, module_info, client_secret):
    """Cria script de teste simples para o módulo"""
    
    test_content = f'''#!/usr/bin/env python3
"""
Teste simples de integração Keycloak para {module_name}
Não requer servidor rodando
"""

import httpx
import sys

KEYCLOAK_URL = "https://keycloak.gsi.srv.br"
REALM = "bemcuidar"
CLIENT_ID = "{module_info['client_id']}"
CLIENT_SECRET = "{client_secret}"
TEST_USER = "dr.silva@saudeplanner.com.br"
TEST_PASSWORD = "Test@123"

def main():
    print("=" * 80)
    print(f"🧪 TESTE SIMPLES - INTEGRAÇÃO KEYCLOAK - {module_name.upper()}")
    print("=" * 80)
    print()
    
    passed = 0
    total = 4
    
    # TESTE 1: Keycloak acessível
    print("TESTE 1: Verificando se Keycloak está acessível...")
    print("-" * 80)
    try:
        response = httpx.get(f"{{KEYCLOAK_URL}}/realms/{{REALM}}", verify=False, timeout=10)
        if response.status_code == 200:
            print("✅ PASSOU: Keycloak está acessível")
            print(f"   URL: {{KEYCLOAK_URL}}")
            print(f"   Realm: {{REALM}}")
            print(f"   Status: {{response.status_code}}")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {{response.status_code}}")
    except Exception as e:
        print(f"❌ FALHOU: {{e}}")
    print()
    
    # TESTE 2: Token com usuário
    print("TESTE 2: Obtendo token com usuário válido...")
    print("-" * 80)
    try:
        token_url = f"{{KEYCLOAK_URL}}/realms/{{REALM}}/protocol/openid-connect/token"
        data = {{
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": TEST_USER,
            "password": TEST_PASSWORD
        }}
        
        response = httpx.post(token_url, data=data, verify=False, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ PASSOU: Token obtido com sucesso")
            print(f"   Usuário: {{TEST_USER}}")
            print(f"   Token Type: {{token_data.get('token_type')}}")
            print(f"   Expires In: {{token_data.get('expires_in')}} segundos")
            print(f"   Token (primeiros 50 chars): {{token_data.get('access_token', '')[:50]}}...")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {{response.status_code}}")
            print(f"   Response: {{response.text}}")
    except Exception as e:
        print(f"❌ FALHOU: {{e}}")
    print()
    
    # TESTE 3: Credenciais inválidas
    print("TESTE 3: Verificando rejeição de credenciais inválidas...")
    print("-" * 80)
    try:
        response = httpx.post(
            token_url,
            data={{
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "username": "invalid@user.com",
                "password": "wrongpassword"
            }},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ PASSOU: Credenciais inválidas foram rejeitadas")
            print(f"   Status: {{response.status_code}} (Unauthorized)")
            passed += 1
        else:
            print(f"❌ FALHOU: Esperado 401, recebido {{response.status_code}}")
    except Exception as e:
        print(f"❌ FALHOU: {{e}}")
    print()
    
    # TESTE 4: Client credentials
    print("TESTE 4: Verificando configuração do cliente...")
    print("-" * 80)
    try:
        response = httpx.post(
            token_url,
            data={{
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ PASSOU: Cliente configurado corretamente")
            print(f"   Client ID: {{CLIENT_ID}}")
            print(f"   Status: {{response.status_code}}")
            print("   Client Credentials: Habilitado")
            passed += 1
        else:
            print(f"❌ FALHOU: Status {{response.status_code}}")
            print(f"   Response: {{response.text}}")
    except Exception as e:
        print(f"❌ FALHOU: {{e}}")
    print()
    
    # Resumo
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    print(f"✅ Testes que passaram: {{passed}}")
    print(f"❌ Testes que falharam: {{total - passed}}")
    print(f"📈 Total de testes: {{total}}")
    print()
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print()
        print("✅ Keycloak está configurado corretamente")
        print("✅ Autenticação está funcionando")
        print(f"✅ Cliente {{CLIENT_ID}} está OK")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    return test_content

def replicate_to_module(module_name):
    """Replica configuração Keycloak para um módulo"""
    
    print("=" * 80)
    print(f"🔄 REPLICANDO KEYCLOAK PARA: {module_name}")
    print("=" * 80)
    print()
    
    if module_name not in MODULES:
        print(f"❌ Módulo '{module_name}' não encontrado")
        print(f"   Módulos disponíveis: {', '.join(MODULES.keys())}")
        sys.exit(1)
    
    module_info = MODULES[module_name]
    
    # Carregar client secrets
    print("📂 Carregando client secrets...")
    client_secrets = load_client_secrets()
    
    client_id = module_info['client_id']
    if client_id not in client_secrets:
        print(f"❌ Client secret não encontrado para '{client_id}'")
        sys.exit(1)
    
    client_secret = client_secrets[client_id]
    print(f"✅ Client secret encontrado: {client_secret[:10]}...")
    print()
    
    # Diretório do módulo
    module_dir = Path(__file__).parent.parent.parent / module_name
    
    if not module_dir.exists():
        print(f"❌ Diretório do módulo não encontrado: {module_dir}")
        sys.exit(1)
    
    print(f"📁 Diretório do módulo: {module_dir}")
    print()
    
    # Criar .env.keycloak
    print("📝 Criando .env.keycloak...")
    env_file = module_dir / ".env.keycloak"
    env_content = create_env_keycloak(module_name, module_info, client_secret)
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Criado: {env_file}")
    print()
    
    # Criar teste_simples.py
    print("📝 Criando teste_simples.py...")
    test_file = module_dir / "teste_simples.py"
    test_content = create_test_simple(module_name, module_info, client_secret)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ Criado: {test_file}")
    print()
    
    print("=" * 80)
    print("🎉 REPLICAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print()
    print(f"Módulo: {module_name}")
    print(f"Client ID: {client_id}")
    print(f"Port: {module_info['port']}")
    print()
    print("📋 Próximos passos:")
    print(f"  1. cd {module_dir}")
    print(f"  2. python teste_simples.py")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python replicate_keycloak_to_module.py <module_name>")
        print()
        print("Módulos disponíveis:")
        for module in MODULES.keys():
            print(f"  - {module}")
        sys.exit(1)
    
    module_name = sys.argv[1]
    replicate_to_module(module_name)

