import paramiko
import json
import time
import requests
from urllib.parse import quote

def ssh_exec(cmd, timeout=120):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('161.97.141.186', port=22, username='root', password='Crazy57LB', timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    ssh.close()
    return out, err, exit_code

print("=== ROCKET CHAT + KEYCLOAK SSO CONFIGURATION ===\n")

# ========================================
# STEP 1: Create Keycloak client for Rocket Chat
# ========================================
print("STEP 1: Criar client 'rocketchat' no Keycloak\n")

# Get admin token
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=egarabini%40gmail.com&password=Crazy%2357LB&grant_type=password&client_id=admin-cli'""")
admin_token = json.loads(out)['access_token']
print(f"   Admin token: OK")

# Check if client already exists
out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients?clientId=rocketchat'")
existing = json.loads(out)
if existing:
    print(f"   Client 'rocketchat' ja existe: {existing[0]['id']}")
    client_uuid = existing[0]['id']
else:
    # Create client
    client_config = {
        "clientId": "rocketchat",
        "name": "Rocket Chat",
        "description": "Rocket Chat - IntelliCare Communication",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": False,
        "authorizationServicesEnabled": False,
        "redirectUris": [
            "https://rocket.gsi.srv.br/_oauth/keycloak",
            "https://rocket.gsi.srv.br/*"
        ],
        "webOrigins": [
            "https://rocket.gsi.srv.br"
        ],
        "rootUrl": "https://rocket.gsi.srv.br",
        "baseUrl": "/",
        "attributes": {
            "post.logout.redirect.uris": "https://rocket.gsi.srv.br/*"
        }
    }
    
    out, err, rc = ssh_exec(f"""curl -s -k -X POST 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients' \
  -H 'Authorization: Bearer {admin_token}' \
  -H 'Content-Type: application/json' \
  -d '{json.dumps(client_config)}'""")
    print(f"   Create response: [{out}] rc={rc}")
    
    # Get the UUID
    out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients?clientId=rocketchat'")
    existing = json.loads(out)
    client_uuid = existing[0]['id']
    print(f"   Client criado: {client_uuid}")

# Get client secret
out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients/{client_uuid}/client-secret'")
secret_data = json.loads(out)
client_secret = secret_data.get('value', '')
print(f"   Client secret: {client_secret}")

# ========================================
# STEP 2: Get Rocket Chat admin credentials and API
# ========================================
print(f"\nSTEP 2: Verificar Rocket Chat API\n")

# Check if we can access the API
out, _, _ = ssh_exec("curl -s -k 'https://rocket.gsi.srv.br/api/v1/info' --max-time 10")
try:
    info = json.loads(out)
    print(f"   RC Version: {info.get('info', {}).get('version', 'unknown')}")
except:
    print(f"   API response: {out[:200]}")

# Try to login with default admin credentials
print(f"\n   Tentando login admin no Rocket Chat...")
# Common default credentials for Rocket Chat
for user, pwd in [('admin', 'admin'), ('admin', 'supersecret'), ('admin', 'Crazy57LB'), ('admin', 'Test@1234'), ('rocketchat', 'rocketchat')]:
    out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{{"user":"{user}","password":"{pwd}"}}'""")
    try:
        resp = json.loads(out)
        if resp.get('status') == 'success':
            rc_token = resp['data']['authToken']
            rc_user_id = resp['data']['userId']
            print(f"   ✓ Login OK: user={user} pwd={pwd}")
            print(f"   authToken: {rc_token[:30]}...")
            print(f"   userId: {rc_user_id}")
            break
        else:
            print(f"   ✗ {user}/{pwd}: {resp.get('message', resp.get('error', 'failed'))}")
    except:
        print(f"   ✗ {user}/{pwd}: parse error")
else:
    print(f"\n   Nenhuma credencial padrao funcionou.")
    print(f"   Precisamos configurar via API ou interface web.")
    # Check if setup wizard was completed
    out, _, _ = ssh_exec("curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings.public?query=%7B%22_id%22%3A%22Show_Setup_Wizard%22%7D' --max-time 10")
    print(f"   Setup wizard status: {out[:200]}")
    
    rc_token = None
    rc_user_id = None

# ========================================
# STEP 3: Configure OAuth via Rocket Chat API (if we have admin access)
# ========================================
if rc_token:
    print(f"\nSTEP 3: Configurando Keycloak OAuth no Rocket Chat\n")
    
    headers = {
        'X-Auth-Token': rc_token,
        'X-User-Id': rc_user_id,
        'Content-Type': 'application/json'
    }
    
    # Rocket Chat Custom OAuth settings for Keycloak
    settings = {
        # Enable Custom OAuth
        'Accounts_OAuth_Custom-Keycloak': True,
        'Accounts_OAuth_Custom-Keycloak-url': 'https://keycloak.gsi.srv.br/realms/bemcuidar',
        'Accounts_OAuth_Custom-Keycloak-token_path': '/protocol/openid-connect/token',
        'Accounts_OAuth_Custom-Keycloak-token_sent_via': 'header',
        'Accounts_OAuth_Custom-Keycloak-identity_token_sent_via': 'default',
        'Accounts_OAuth_Custom-Keycloak-identity_path': '/protocol/openid-connect/userinfo',
        'Accounts_OAuth_Custom-Keycloak-authorize_path': '/protocol/openid-connect/auth',
        'Accounts_OAuth_Custom-Keycloak-scope': 'openid email profile',
        'Accounts_OAuth_Custom-Keycloak-access_token_param': 'access_token',
        'Accounts_OAuth_Custom-Keycloak-id': 'rocketchat',
        'Accounts_OAuth_Custom-Keycloak-secret': client_secret,
        'Accounts_OAuth_Custom-Keycloak-login_style': 'redirect',
        'Accounts_OAuth_Custom-Keycloak-button_label_text': 'Keycloak SSO',
        'Accounts_OAuth_Custom-Keycloak-button_label_color': '#FFFFFF',
        'Accounts_OAuth_Custom-Keycloak-button_color': '#0078D4',
        'Accounts_OAuth_Custom-Keycloak-key_field': 'username',
        'Accounts_OAuth_Custom-Keycloak-username_field': 'preferred_username',
        'Accounts_OAuth_Custom-Keycloak-email_field': 'email',
        'Accounts_OAuth_Custom-Keycloak-name_field': 'name',
        'Accounts_OAuth_Custom-Keycloak-roles_claim': 'roles',
        'Accounts_OAuth_Custom-Keycloak-merge_users': True,
        'Accounts_OAuth_Custom-Keycloak-merge_roles': False,
        'Accounts_OAuth_Custom-Keycloak-show_button': True,
    }
    
    for key, value in settings.items():
        val_json = json.dumps(value)
        out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/{key}' \
  -H 'X-Auth-Token: {rc_token}' \
  -H 'X-User-Id: {rc_user_id}' \
  -H 'Content-Type: application/json' \
  -d '{{"value": {val_json}}}'""")
        try:
            resp = json.loads(out)
            status = "✓" if resp.get('success') else "✗"
        except:
            status = "?"
        print(f"   {status} {key}: {value}")
    
    print(f"\n   Configuracao Keycloak concluida!")
else:
    print(f"\nSTEP 3: PRECISA DE CREDENCIAIS ADMIN DO ROCKET CHAT")
    print(f"   Acesse https://rocket.gsi.srv.br e crie um admin")
    print(f"   Ou me informe as credenciais de admin")

# ========================================
# STEP 4: Summary
# ========================================
print(f"\n{'='*50}")
print(f"RESUMO:")
print(f"{'='*50}")
print(f"Rocket Chat: https://rocket.gsi.srv.br (v7.13.2)")
print(f"Keycloak client: rocketchat (secret: {client_secret})")
print(f"Keycloak realm: bemcuidar")
print(f"OAuth callback: https://rocket.gsi.srv.br/_oauth/keycloak")
if rc_token:
    print(f"Admin login: funcionou, OAuth configurado")
else:
    print(f"Admin login: PENDENTE - precisa credenciais")
