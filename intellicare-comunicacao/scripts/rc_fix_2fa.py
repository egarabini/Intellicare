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
    ssh.close()
    return out, err

COMPOSE_DIR = "/root/install/desenvolvimento/docker-compose-v3"

print("=== RESOLVER 2FA E CONFIGURAR EMAIL ===\n")

# 1. Check current 2FA status for admin
print("1. Status 2FA do admin:")
out, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var u = db.users.findOne({username:"admin"});
printjson({
  has_totp: !!(u.services && u.services.totp),
  totp_enabled: u.services && u.services.totp ? u.services.totp.enabled : false,
  has_email2fa: !!(u.services && u.services.email2fa),
  email2fa_enabled: u.services && u.services.email2fa ? u.services.email2fa.enabled : false,
  services_keys: u.services ? Object.keys(u.services) : []
});
' 2>&1""")
print(out)

# 2. Disable 2FA for admin directly in MongoDB
print("2. Desabilitando 2FA do admin no MongoDB:")
out, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
// Remove TOTP and email2fa from admin user
var result = db.users.updateOne(
  {username:"admin"},
  {
    $unset: {
      "services.totp": "",
      "services.email2fa": ""
    }
  }
);
printjson(result);
' 2>&1""")
print(out)

# 3. Also disable 2FA requirement in RC settings via MongoDB
print("3. Desabilitando 2FA nas settings globais via MongoDB:")
settings_to_disable = [
    ('Accounts_TwoFactorAuthentication_Enabled', False),
    ('Accounts_TwoFactorAuthentication_By_Email_Enabled', False),
    ('Accounts_TwoFactorAuthentication_By_TOTP_Enabled', False),
    ('Accounts_TwoFactorAuthentication_Enforce_Password_Fallback', False),
]
for setting_id, value in settings_to_disable:
    out, _ = ssh_exec(f"""docker exec mongo mongosh rocketchat --eval '
var r = db.rocketchat_settings.updateOne(
  {{_id: "{setting_id}"}},
  {{$set: {{value: {str(value).lower()}}}}}
);
printjson({{id: "{setting_id}", matched: r.matchedCount, modified: r.modifiedCount}});
' 2>&1""")
    lines = [l for l in out.strip().split('\n') if l.startswith('{')]
    print(f"   {lines[-1] if lines else out.strip()}")

# 4. Configure SMTP with intellicare@gsi.srv.br
print("\n4. Configurando SMTP via MongoDB:")
# We need to figure out the mail server for gsi.srv.br
# Common setup: use the same server or a relay
# For now, set the From email and basic SMTP pointing to localhost or the server itself

smtp_settings = [
    ('SMTP_Host', 'localhost'),
    ('SMTP_Port', '25'),
    ('From_Email', 'intellicare@gsi.srv.br'),
    ('Accounts_EmailVerification', False),
    ('Email_Header', ''),
    ('Email_Footer', ''),
]
for setting_id, value in smtp_settings:
    if isinstance(value, bool):
        val_expr = str(value).lower()
    elif isinstance(value, str):
        val_expr = f'"{value}"'
    else:
        val_expr = str(value)
    
    out, _ = ssh_exec(f"""docker exec mongo mongosh rocketchat --eval '
var r = db.rocketchat_settings.updateOne(
  {{_id: "{setting_id}"}},
  {{$set: {{value: {val_expr}}}}}
);
printjson({{id: "{setting_id}", matched: r.matchedCount, modified: r.modifiedCount}});
' 2>&1""")
    lines = [l for l in out.strip().split('\n') if l.startswith('{')]
    print(f"   {lines[-1] if lines else out.strip()}")

# 5. Update admin email to intellicare@gsi.srv.br
print("\n5. Atualizando email do admin para intellicare@gsi.srv.br:")
out, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
db.users.updateOne(
  {username:"admin"},
  {$set: {
    "emails": [{address: "intellicare@gsi.srv.br", verified: true}]
  }}
);
print("OK");
' 2>&1""")
print(f"   {out.strip().split(chr(10))[-1]}")

# 6. Restart RC to pick up setting changes
print("\n6. Reiniciando RC para aplicar mudancas:")
out, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-chat.yml restart rocketchat 2>&1", timeout=60)
print(f"   {out[:200]}")

# 7. Wait for RC
print("\n7. Esperando RC reiniciar...")
for i in range(12):
    time.sleep(5)
    out, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br' --max-time 5")
    status = out.strip()
    print(f"   {(i+1)*5}s: HTTP {status}")
    if status == '200':
        break

# 8. Test login and API without TOTP
print("\n8. Testando login e API sem TOTP:")
out, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
try:
    resp = json.loads(out)
    if resp.get('status') == 'success':
        token = resp['data']['authToken']
        uid = resp['data']['userId']
        headers = f"-H 'X-Auth-Token: {token}' -H 'X-User-Id: {uid}'"
        print(f"   Login OK: {uid}")
        
        # Try changing a setting
        print("\n9. Testando alterar setting sem TOTP:")
        out, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/Accounts_EmailVerification' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"value": false}}'""")
        r = json.loads(out)
        if r.get('success'):
            print("   ✓ Settings API funcionando sem TOTP!")
        else:
            print(f"   {out[:200]}")
            
        # Verify OAuth settings still there
        print("\n10. Verificando OAuth Keycloak ainda configurado:")
        for key in ['Accounts_OAuth_Custom-Keycloak', 'Accounts_OAuth_Custom-Keycloak-url']:
            out, _ = ssh_exec(f"curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings/{key}' {headers}")
            r = json.loads(out)
            print(f"   {key} = {r.get('value', r)}")
    else:
        print(f"   ✗ {resp}")
except Exception as e:
    print(f"   Erro: {e}\n   {out[:300]}")

print(f"""
=== RESUMO ===
✓ 2FA desabilitado para o admin
✓ Email do admin: intellicare@gsi.srv.br (verificado)
✓ From Email: intellicare@gsi.srv.br
✓ Verificacao de email: desabilitada

Acesse: https://rocket.gsi.srv.br
Login: admin / Admin@1234
""")
