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

print("=== FIX ADMIN PASSWORD ===\n")

# 1. Generate bcrypt hash inside rocketchat container (has Node.js with bcrypt)
print("1. Gerando hash bcrypt dentro do container RC:")
out, _, _ = ssh_exec(r"""docker exec rocketchat node -e "
const crypto = require('crypto');
// SHA256 first (Rocket Chat hashes password with SHA256 before bcrypt)
const sha256 = crypto.createHash('sha256').update('Admin@1234').digest('hex');
console.log('SHA256: ' + sha256);
// Now we need bcrypt - check if available
try {
  const bcrypt = require('bcrypt');
  const hash = bcrypt.hashSync(sha256, 10);
  console.log('HASH:' + hash);
} catch(e) {
  console.log('NO_BCRYPT:' + e.message);
  // Try bcryptjs
  try {
    const bcrypt = require('bcryptjs');
    const hash = bcrypt.hashSync(sha256, 10);
    console.log('HASH:' + hash);
  } catch(e2) {
    console.log('NO_BCRYPTJS:' + e2.message);
  }
}
" 2>&1""")
print(out[:500])

if 'HASH:' in out:
    bcrypt_hash = out.split('HASH:')[1].strip().split('\n')[0]
    print(f"\n   Hash: {bcrypt_hash}")
    
    # 2. Update the admin user's password in MongoDB
    print("\n2. Atualizando senha no MongoDB:")
    # Need to escape $ for shell
    hash_escaped = bcrypt_hash.replace('$', '\\$')
    
    out, _, _ = ssh_exec(f"""docker exec mongo mongosh rocketchat --eval '
db.users.updateOne(
  {{username: "admin"}},
  {{
    \\$set: {{
      "services.password.bcrypt": "{bcrypt_hash}",
      "services.password.reset": undefined
    }}
  }}
)
' 2>&1""")
    print(out[:500])
    
    # Alternative approach - use heredoc to avoid escaping issues
    if 'error' in out.lower() or 'syntaxerror' in out.lower():
        print("\n   Tentando abordagem alternativa...")
        script = f"""
var hash = "{bcrypt_hash}";
var result = db.users.updateOne(
  {{username: "admin"}},
  {{$set: {{"services.password.bcrypt": hash}}}}
);
printjson(result);
"""
        # Write script to file inside mongo container
        ssh_exec(f"docker exec mongo bash -c 'cat > /tmp/fix_pw.js << JSEOF\n{script}\nJSEOF'")
        out, _, _ = ssh_exec("docker exec mongo mongosh rocketchat /tmp/fix_pw.js 2>&1")
        print(out[:500])
else:
    print("\n   Tentando abordagem direta com env vars...")
    # Use ADMIN_USERNAME, ADMIN_PASS, ADMIN_EMAIL env vars
    # Delete the manually created user first
    ssh_exec("""docker exec mongo mongosh rocketchat --eval 'db.users.deleteOne({username:"admin"})' 2>&1""")
    
    # Restart RC with admin env vars
    print("\n   Reiniciando RC com ADMIN_USERNAME/ADMIN_PASS...")
    # Add env vars to docker-compose or use docker run
    out, _, _ = ssh_exec(f"""cd {COMPOSE_DIR} && docker stop rocketchat 2>&1""")
    time.sleep(2)
    
    # Run with env vars
    out, _, _ = ssh_exec(f"""docker run -d --name rocketchat_temp \
  --network docker-compose-v3_gsi_network \
  -e PORT=3000 \
  -e ROOT_URL=https://rocket.gsi.srv.br \
  -e MONGO_URL='mongodb://mongo:27017/rocketchat?replicaSet=rs0' \
  -e MONGO_OPLOG_URL='mongodb://mongo:27017/local?replicaSet=rs0' \
  -e OVERWRITE_SETTING_Show_Setup_Wizard=completed \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASS=Admin@1234 \
  -e ADMIN_EMAIL=admin@rocket.gsi.srv.br \
  rocketchat/rocket.chat:latest 2>&1""")
    print(f"   Temp container: {out[:200]}")

# 3. Test login
print("\n3. Testando login (aguardando 10s):")
time.sleep(10)
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
try:
    resp = json.loads(out)
    if resp.get('status') == 'success':
        print(f"   ✓ Login OK!")
        print(f"   authToken: {resp['data']['authToken'][:30]}...")
    else:
        print(f"   ✗ {resp.get('message', resp.get('error', 'failed'))}")
        
        # Maybe RC needs restart to pick up the new user
        print("\n   Reiniciando RC...")
        ssh_exec("docker restart rocketchat 2>&1")
        time.sleep(30)
        
        out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
        resp = json.loads(out)
        if resp.get('status') == 'success':
            print(f"   ✓ Login OK apos restart!")
        else:
            print(f"   ✗ Ainda falhou: {resp.get('message', 'failed')}")
            
            # Verify what's in MongoDB
            out3, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var u = db.users.findOne({username:"admin"});
printjson({id:u._id, username:u.username, hasPassword:!!u.services.password, bcryptLen:u.services.password.bcrypt.length, roles:u.roles});
' 2>&1""")
            print(f"   MongoDB user: {out3[:500]}")
except:
    print(f"   Erro: {out[:300]}")

print("\n=== END ===")
