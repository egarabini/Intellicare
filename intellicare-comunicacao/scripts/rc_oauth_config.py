import paramiko
import json
import time

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

print("=== CONFIGURAR KEYCLOAK OAUTH NO ROCKET CHAT ===\n")

# 1. Login
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
resp = json.loads(out)
token = resp['data']['authToken']
uid = resp['data']['userId']
print(f"1. Login OK: {uid}")

headers = f"-H 'X-Auth-Token: {token}' -H 'X-User-Id: {uid}'"

# 2. Check current Keycloak OAuth settings after addCustomOAuth
print("\n2. Verificando settings Keycloak criadas:")
out, _, _ = ssh_exec(f"""curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings?count=500' \
  {headers}""")
r = json.loads(out)
kc_settings = [s for s in r.get('settings', []) if 'Keycloak' in s.get('_id', '') or 'keycloak' in s.get('_id', '')]
print(f"   Total: {len(r.get('settings',[]))}, Keycloak: {len(kc_settings)}")
for s in kc_settings:
    print(f"   {s['_id']} = {s.get('value','')}")

# 3. Apply all settings
print("\n3. Aplicando configuracoes:")

client_secret = "DEjBj1bXQtyxXHjICpeZZAC2lZvXhLQw"

settings = {
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
    'Accounts_OAuth_Custom-Keycloak-button_label_text': 'Login com Keycloak',
    'Accounts_OAuth_Custom-Keycloak-button_label_color': '#FFFFFF',
    'Accounts_OAuth_Custom-Keycloak-button_color': '#13679A',
    'Accounts_OAuth_Custom-Keycloak-key_field': 'username',
    'Accounts_OAuth_Custom-Keycloak-username_field': 'preferred_username',
    'Accounts_OAuth_Custom-Keycloak-email_field': 'email',
    'Accounts_OAuth_Custom-Keycloak-name_field': 'name',
    'Accounts_OAuth_Custom-Keycloak-roles_claim': 'roles',
    'Accounts_OAuth_Custom-Keycloak-merge_users': True,
    'Accounts_OAuth_Custom-Keycloak-merge_roles': False,
    'Accounts_OAuth_Custom-Keycloak-show_button': True,
}

success = 0
fail = 0
for key, value in settings.items():
    val_json = json.dumps(value)
    out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/{key}' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"value": {val_json}}}'""")
    try:
        r = json.loads(out)
        if r.get('success'):
            success += 1
            print(f"   OK {key}")
        else:
            fail += 1
            print(f"   FAIL {key}: {out[:150]}")
    except:
        fail += 1
        print(f"   ERR {key}: {out[:150]}")

print(f"\n   Resultado: {success} OK, {fail} falhas")

# 4. Verify settings were applied
print("\n4. Verificando settings aplicadas:")
out, _, _ = ssh_exec(f"""curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings?count=500' \
  {headers}""")
r = json.loads(out)
kc_settings = [s for s in r.get('settings', []) if 'Keycloak' in s.get('_id', '') or 'keycloak' in s.get('_id', '')]
for s in kc_settings:
    val = s.get('value', '')
    if isinstance(val, str) and len(val) > 60:
        val = val[:60] + '...'
    print(f"   {s['_id']} = {val}")

# 5. Test if the login page shows the keycloak button
print("\n5. Verificando pagina de login:")
out, _, _ = ssh_exec("curl -s -k 'https://rocket.gsi.srv.br' | grep -i -o 'keycloak\\|oauth\\|custom-oauth' | head -5")
if out.strip():
    print(f"   Encontrado: {out.strip()}")
else:
    print("   (HTML nao contém referencia direta - normal para SPA)")

print(f"\n=== CONFIGURACAO CONCLUIDA ===")
print(f"URL Rocket Chat: https://rocket.gsi.srv.br")
print(f"Admin: admin / Admin@1234")
print(f"Keycloak SSO: Botao 'Login com Keycloak' na pagina de login")
print(f"Keycloak test user: admin@saudeplanner.com.br / Test@1234")
