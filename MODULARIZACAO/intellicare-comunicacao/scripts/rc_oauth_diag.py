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

print("=== DIAGNOSTICO OAuth Settings ===\n")

# 1. Login
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
resp = json.loads(out)
token = resp['data']['authToken']
uid = resp['data']['userId']
print(f"Token: {token[:20]}..., UserId: {uid}")

headers = f"-H 'X-Auth-Token: {token}' -H 'X-User-Id: {uid}'"

# 2. Check what error we get from settings API
print("\n2. Testando settings API com detalhes de erro:")
test_settings = [
    'Accounts_OAuth_Custom-Keycloak',
    'Accounts_OAuth_Custom-Keycloak-url',
]
for s in test_settings:
    out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/{s}' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"value": true}}'""")
    print(f"   {s}: {out[:200]}")

# 3. Try GET on existing settings to understand naming
print("\n3. Buscando settings OAuth existentes:")
out, _, _ = ssh_exec(f"""curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings?query=%7B%22_id%22%3A%7B%22%24regex%22%3A%22OAuth%22%7D%7D&count=50' \
  {headers}""")
try:
    r = json.loads(out)
    if r.get('settings'):
        for s in r['settings']:
            print(f"   {s['_id']}: {s.get('value', '')}")
    else:
        print(f"   resp: {out[:500]}")
except:
    print(f"   Parse error: {out[:500]}")

# 4. Try to add Custom OAuth via admin endpoint
print("\n4. Tentando adicionar Custom OAuth 'keycloak':")
out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings.addCustomOAuth' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"name": "keycloak"}}'""")
print(f"   {out[:300]}")

# 5. Try the settings.update approach
print("\n5. Tentando settings.update:")
out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/Accounts_OAuth_Custom-Keycloak' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"value": true}}'""")
print(f"   {out[:200]}")

# 6. Try method call approach (DDP-style)
print("\n6. Tentando method.call saveOAuthServiceConfiguration:")
out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/method.call/addOAuthService' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"message": "[\\"keycloak\\"]"}}'""")
print(f"   {out[:400]}")

# 7. Check RC version and API info
print("\n7. Info RC:")
out, _, _ = ssh_exec(f"curl -s -k 'https://rocket.gsi.srv.br/api/v1/info' {headers}")
try:
    r = json.loads(out)
    print(f"   Version: {r.get('info',{}).get('version', 'unknown')}")
except:
    print(f"   {out[:200]}")

# 8. List all current settings with OAuth in _id
print("\n8. Listando settings com 'Custom' no id:")
out, _, _ = ssh_exec(f"""curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings?count=100' \
  {headers} \
  -H 'Content-Type: application/json'""")
try:
    r = json.loads(out)
    if r.get('settings'):
        oauth_settings = [s for s in r['settings'] if 'OAuth' in s.get('_id', '') or 'oauth' in s.get('_id', '')]
        print(f"   Total settings: {len(r['settings'])}, OAuth: {len(oauth_settings)}")
        for s in oauth_settings[:30]:
            val = s.get('value', '')
            if isinstance(val, str) and len(val) > 50:
                val = val[:50] + '...'
            print(f"   {s['_id']} = {val}")
    else:
        print(f"   {out[:300]}")
except:
    print(f"   {out[:300]}")

print("\n=== END ===")
