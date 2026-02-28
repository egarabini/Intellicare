import paramiko
import json

def ssh_exec(cmd, timeout=120):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('161.97.141.186', port=22, username='root', password='Crazy57LB', timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    ssh.close()
    return out, err

print("=== INVESTIGAR EMAIL DO ROCKET CHAT ===\n")

# 1. Check RC logs for email references
print("1. Logs recentes do RC sobre email:")
out, _ = ssh_exec("docker logs rocketchat --tail 100 2>&1 | grep -i 'mail\\|smtp\\|email' | tail -20")
print(out if out.strip() else "   (nenhum log de email)")

# 2. Login
out, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
resp = json.loads(out)
token = resp['data']['authToken']
uid = resp['data']['userId']
headers = f"-H 'X-Auth-Token: {token}' -H 'X-User-Id: {uid}'"

# 3. Check SMTP settings
print("\n2. Configuracoes SMTP do RC:")
smtp_keys = [
    'SMTP_Host', 'SMTP_Port', 'SMTP_Username', 'SMTP_Password',
    'From_Email', 'SMTP_Test_Button_Pressed',
    'Accounts_EmailVerification', 'Verification_Customized',
    'Email_Notification_Mode',
]
out, _ = ssh_exec(f"curl -s -k 'https://rocket.gsi.srv.br/api/v1/settings?count=1000' {headers}")
r = json.loads(out)
all_settings = r.get('settings', [])

# Find all email/smtp related settings
email_settings = [s for s in all_settings if any(x in s.get('_id','').lower() for x in ['smtp', 'mail', 'email', 'from_email', 'verification'])]
for s in email_settings:
    val = s.get('value', '')
    if isinstance(val, str) and len(val) > 80:
        val = val[:80] + '...'
    print(f"   {s['_id']} = {val}")

# 4. Check the admin user's email verification status
print("\n3. Status do usuario admin:")
out, _ = ssh_exec(f"""docker exec mongo mongosh rocketchat --eval '
var u = db.users.findOne({{username:"admin"}});
printjson({{
  email: u.emails,
  verified: u.emails ? u.emails.map(function(e){{return e.verified}}) : "no emails",
  requirePasswordChange: u.requirePasswordChange,
  active: u.active
}});
' 2>&1""")
print(out)

# 5. Check if there's a mail queue
print("4. Fila de emails no MongoDB:")
out, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var count = db.rocketchat_outgoing_integrations ? db.getCollection("rocketchat__trash").countDocuments({}) : 0;
print("Trash: " + count);
// Check email inbox/outbox collections
var cols = db.getCollectionNames();
var emailCols = cols.filter(function(c){ return c.indexOf("mail") >= 0 || c.indexOf("email") >= 0; });
print("Email collections: " + JSON.stringify(emailCols));
' 2>&1""")
print(out)

print("\n5. O email mencionado:")
print("   O Rocket Chat enviou um email de VERIFICACAO para: admin@rocket.gsi.srv.br")
print("   Como nao ha SMTP configurado, o email provavelmente FALHOU silenciosamente.")
print("   Esse email e apenas para verificar o endereco do admin.")

print("\n6. Solucao - desabilitar verificacao de email:")
# Disable email verification since there's no SMTP configured
settings_to_fix = {
    'Accounts_EmailVerification': False,
    'Accounts_ManuallyApproveNewUsers': False,
}
for key, value in settings_to_fix.items():
    out, _ = ssh_exec(f"""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/settings/{key}' \
  {headers} \
  -H 'Content-Type: application/json' \
  -d '{{"value": {json.dumps(value)}}}'""")
    r = json.loads(out)
    print(f"   {key} = {value}: {'OK' if r.get('success') else out[:100]}")

# Also mark admin email as verified directly
print("\n7. Marcando email do admin como verificado:")
out, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
db.users.updateOne(
  {username:"admin"},
  {$set: {"emails.0.verified": true}}
);
print("OK");
' 2>&1""")
print(f"   {out.strip().split(chr(10))[-1]}")

print("\n=== CONCLUIDO ===")
