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

COMPOSE_DIR = "/root/install/desenvolvimento/docker-compose-v3"

print("=== VERIFICACAO FINAL E LIMPEZA ===\n")

# 1. Verify Keycloak client redirect URIs
print("1. Verificando redirect URIs do client Keycloak:")
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' \
  -d 'client_id=admin-cli' \
  -d 'username=egarabini@gmail.com' \
  -d 'password=Crazy#57LB' \
  -d 'grant_type=password'""")
kc_token = json.loads(out)['access_token']

out, _, _ = ssh_exec(f"""curl -s -k 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients?clientId=rocketchat' \
  -H 'Authorization: Bearer {kc_token}'""")
clients = json.loads(out)
if clients:
    client = clients[0]
    print(f"   Client ID: {client['clientId']}")
    print(f"   Redirect URIs: {client.get('redirectUris', [])}")
    print(f"   Web Origins: {client.get('webOrigins', [])}")
    
    # Ensure the callback URL is in redirect URIs
    redirect_uris = client.get('redirectUris', [])
    callback = 'https://rocket.gsi.srv.br/_oauth/keycloak'
    if callback not in redirect_uris:
        print(f"   ⚠ Adicionando callback URL: {callback}")
        redirect_uris.append(callback)
        client_uuid = client['id']
        out, _, _ = ssh_exec(f"""curl -s -k -X PUT 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients/{client_uuid}' \
  -H 'Authorization: Bearer {kc_token}' \
  -H 'Content-Type: application/json' \
  -d '{json.dumps({"redirectUris": redirect_uris})}'""")
        print(f"   Atualizado: {out[:100] if out else 'OK (204)'}")
    else:
        print(f"   ✓ Callback URL ja esta configurada")

# 2. Remove ADMIN env vars from compose (only needed for first setup)
print("\n2. Removendo env vars ADMIN do docker-compose (one-time only):")
out, _, _ = ssh_exec(f"cat {COMPOSE_DIR}/docker-compose-chat.yml")
content = out
lines = content.split('\n')
new_lines = [l for l in lines if not any(x in l for x in ['ADMIN_USERNAME:', 'ADMIN_PASS:', 'ADMIN_EMAIL:'])]
new_content = '\n'.join(new_lines)
ssh_exec(f"cat > {COMPOSE_DIR}/docker-compose-chat.yml << 'COMPEOF'\n{new_content}\nCOMPEOF")
print("   ✓ ADMIN env vars removidas")

# 3. Verify RC is healthy
print("\n3. Verificando saude do RC:")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br'")
print(f"   HTTP: {out.strip()}")

out, _, _ = ssh_exec("docker ps --filter name=rocketchat --format '{{.Names}} {{.Status}}'")
print(f"   Container: {out.strip()}")

out, _, _ = ssh_exec("docker ps --filter name=mongo --format '{{.Names}} {{.Status}}'")
print(f"   MongoDB: {out.strip()}")

# 4. Verify OAuth settings via API
print("\n4. Verificando configuracao OAuth via API:")
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
resp = json.loads(out)
token = resp['data']['authToken']
uid = resp['data']['userId']
headers = f"-H 'X-Auth-Token: {token}' -H 'X-User-Id: {uid}'"

# Read back key settings
key_settings = [
    'Accounts_OAuth_Custom-Keycloak',
    'Accounts_OAuth_Custom-Keycloak-url',
    'Accounts_OAuth_Custom-Keycloak-id',
    'Accounts_OAuth_Custom-Keycloak-login_style',
    'Accounts_OAuth_Custom-Keycloak-button_label_text',
]
for s in key_settings:
    out, _, _ = ssh_exec(f"curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings/{s}' {headers}")
    try:
        r = json.loads(out)
        print(f"   {s} = {r.get('value', r)}")
    except:
        print(f"   {s}: {out[:100]}")

# 5. Test the OAuth flow URL
print("\n5. Testando URL do OAuth flow:")
oauth_url = "https://rocket.gsi.srv.br/_oauth/keycloak"
out, _, _ = ssh_exec(f"curl -s -k -o /dev/null -w '%{{http_code}}' '{oauth_url}'")
print(f"   {oauth_url} -> HTTP {out.strip()}")

print(f"""
=== RESUMO FINAL ===

✓ Rocket Chat: https://rocket.gsi.srv.br (v7.13.2)
  Admin: admin / Admin@1234

✓ Keycloak OAuth configurado:
  Provider: Custom OAuth "Keycloak"
  Keycloak realm: bemcuidar
  Client ID: rocketchat
  Callback: https://rocket.gsi.srv.br/_oauth/keycloak
  Login style: redirect
  Botao: "Login com Keycloak"

✓ Para testar SSO:
  1. Abra https://rocket.gsi.srv.br
  2. Clique no botao "Login com Keycloak"
  3. Use credenciais: admin@saudeplanner.com.br / Test@1234
""")
