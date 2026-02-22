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

print("=== FIX: CRIAR ADMIN VIA ENV VARS ===\n")

# 1. Cleanup temp container
print("1. Limpando container temporario:")
ssh_exec("docker stop rocketchat_temp 2>/dev/null; docker rm rocketchat_temp 2>/dev/null")
print("   OK")

# 2. Check if the temp container already created the admin user  
print("\n2. Verificando se admin foi criado pelo container temp:")
out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var u = db.users.findOne({username:"admin"});
if(u) { printjson({id:u._id, username:u.username, roles:u.roles, hasPw:!!u.services&&!!u.services.password}); }
else { print("NO_ADMIN"); }
' 2>&1""")
print(out[:500])

# 3. The proper approach: add ADMIN env vars to docker-compose and restart
print("\n3. Adicionando env vars de admin ao docker-compose-chat.yml:")
ts = int(time.time())
ssh_exec(f"cp {COMPOSE_DIR}/docker-compose-chat.yml {COMPOSE_DIR}/docker-compose-chat.yml.backup.{ts}")

# Read current file
out, _, _ = ssh_exec(f"cat {COMPOSE_DIR}/docker-compose-chat.yml")
compose_content = out

# Add ADMIN env vars to the rocketchat service  
if 'ADMIN_USERNAME' not in compose_content:
    # Add after OVERWRITE_SETTING_Show_Setup_Wizard line
    old_line = '      OVERWRITE_SETTING_Show_Setup_Wizard: "completed"'
    new_lines = '''      OVERWRITE_SETTING_Show_Setup_Wizard: "completed"
      ADMIN_USERNAME: admin
      ADMIN_PASS: "Admin@1234"
      ADMIN_EMAIL: admin@rocket.gsi.srv.br'''
    
    new_content = compose_content.replace(old_line, new_lines)
    
    # Write back
    ssh_exec(f"cat > {COMPOSE_DIR}/docker-compose-chat.yml << 'COMPEOF'\n{new_content}\nCOMPEOF")
    print("   Env vars adicionadas")
else:
    print("   Env vars ja existem")

# Verify
out, _, _ = ssh_exec(f"grep -A5 'ADMIN' {COMPOSE_DIR}/docker-compose-chat.yml")
print(f"   {out}")

# 4. Delete the manually created admin user (malformed) so RC can create properly
print("\n4. Removendo admin manual do MongoDB:")
out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var result = db.users.deleteOne({username:"admin"});
printjson(result);
' 2>&1""")
print(out[:300])

# 5. Restart with compose (proper way)
print("\n5. Reiniciando via docker compose:")
out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-chat.yml up -d rocketchat 2>&1", timeout=60)
print(out[:500])

# 6. Wait for startup
print("\n6. Esperando RC iniciar...")
for i in range(18):
    time.sleep(5)
    out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br' --max-time 5 2>/dev/null")
    status = out.strip()
    out2, _, _ = ssh_exec("docker ps --filter name=rocketchat --format '{{.Status}}' 2>/dev/null")
    print(f"   {(i+1)*5}s: HTTP {status} | {out2.strip()}")
    if status == '200':
        break

# 7. Test login
print("\n7. Testando login admin:")
time.sleep(5)
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
try:
    resp = json.loads(out)
    if resp.get('status') == 'success':
        rc_token = resp['data']['authToken']
        rc_user_id = resp['data']['userId']
        print(f"   ✓ LOGIN OK!")
        print(f"   authToken: {rc_token[:30]}...")
        print(f"   userId: {rc_user_id}")
        
        # 8. Configure Keycloak OAuth
        print(f"\n8. Configurando Keycloak OAuth no Rocket Chat:")
        
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
  -H 'X-Auth-Token: {rc_token}' \
  -H 'X-User-Id: {rc_user_id}' \
  -H 'Content-Type: application/json' \
  -d '{{"value": {val_json}}}'""")
            try:
                r = json.loads(out)
                if r.get('success'):
                    success += 1
                else:
                    fail += 1
                    print(f"   ✗ {key}: {r.get('error', r.get('message', 'failed'))}")
            except:
                fail += 1
                print(f"   ✗ {key}: parse error: {out[:100]}")
        
        print(f"\n   Resultado: {success} OK, {fail} falhas")
        
        if success > 0:
            print(f"\n   ✓ Keycloak OAuth configurado no Rocket Chat!")
            print(f"   URL: https://rocket.gsi.srv.br")
            print(f"   Botao 'Login com Keycloak' deve aparecer na tela de login")
    else:
        print(f"   ✗ {resp.get('message', resp.get('error', 'failed'))}")
except Exception as e:
    print(f"   Erro: {e}")
    print(f"   Response: {out[:300]}")

print("\n=== END ===")
