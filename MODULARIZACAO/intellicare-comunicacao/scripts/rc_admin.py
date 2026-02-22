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

print("=== CRIAR ADMIN NO ROCKET CHAT VIA MONGODB ===\n")

# 1. Check existing users
print("1. Usuarios existentes no MongoDB:")
out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
db.users.find({},{username:1,name:1,roles:1,emails:1}).forEach(function(u){
  printjson({username:u.username, name:u.name, roles:u.roles, email:u.emails?u.emails[0].address:""})
})
' 2>&1""")
print(out[:3000])

# 2. Check if there's already an admin
print("\n2. Admins existentes:")
out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
db.users.find({roles:"admin"},{username:1,name:1,emails:1}).forEach(function(u){
  printjson({username:u.username, name:u.name, email:u.emails?u.emails[0].address:""})
})
' 2>&1""")
print(out[:1000])

# 3. Create admin user directly in MongoDB
# Rocket Chat stores bcrypt hashed passwords
# We'll use the RC admin creation via env vars + restart approach
print("\n3. Criando admin via variavel de ambiente:")
# The cleanest way is to use ADMIN_USERNAME, ADMIN_PASS, ADMIN_EMAIL env vars
# on first start. Since RC already started, we'll create via MongoDB directly.

# First, check if we can reset an existing admin password
out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
var admin = db.users.findOne({roles:"admin"});
if(admin) {
  print("ADMIN_FOUND:" + admin.username);
} else {
  print("NO_ADMIN");
}
' 2>&1""")
print(f"   {out.strip()}")

if 'ADMIN_FOUND' in out:
    admin_username = out.split('ADMIN_FOUND:')[1].strip().split('\n')[0]
    print(f"\n   Admin encontrado: {admin_username}")
    print(f"   Resetando senha via MongoDB...")
    
    # Use bcrypt to hash new password - Rocket Chat uses bcrypt with 10 rounds
    # We'll use the RC API approach: set a known bcrypt hash
    # bcrypt hash of "Admin@1234": $2b$10$ + hash
    # Better approach: use the Rocket Chat CLI or env var
    
    # Actually, let's use a simpler approach: set the password via RC's own mechanism
    # We can update the password hash directly in MongoDB
    # bcrypt("Admin@1234") with 10 rounds
    
    # Generate bcrypt hash on the server
    out2, _, _ = ssh_exec("""docker exec rocketchat node -e "
const bcrypt = require('bcrypt');
bcrypt.hash('Admin@1234', 10, function(err, hash) {
  if(err) console.log('ERROR:' + err);
  else console.log('HASH:' + hash);
});
" 2>&1""")
    print(f"   Bcrypt: {out2.strip()}")
    
    if 'HASH:' in out2:
        bcrypt_hash = out2.split('HASH:')[1].strip()
        print(f"   Hash: {bcrypt_hash}")
        
        # Update in MongoDB - escape the $ signs
        bcrypt_escaped = bcrypt_hash.replace("'", "\\'")
        out3, _, _ = ssh_exec(f"""docker exec mongo mongosh rocketchat --eval '
db.users.updateOne(
  {{roles:"admin"}},
  {{$set: {{"services.password.bcrypt": "{bcrypt_escaped}"}}}}
)
' 2>&1""")
        print(f"   Update: {out3[:500]}")
    else:
        # Fallback: try python bcrypt
        print("   Tentando com python3...")
        out2, _, _ = ssh_exec("""docker exec mongo bash -c "python3 -c \\"import bcrypt; print(bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt(10)).decode())\\" 2>/dev/null || echo 'NO_PYTHON'" 2>&1""")
        print(f"   Python bcrypt: {out2.strip()}")
else:
    print("\n   Nenhum admin encontrado. Criando admin via env vars...")
    # Restart RC with admin env vars
    out, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
// Create admin user directly
var userId = "admin_" + new Date().getTime();
db.users.insertOne({
  _id: userId,
  createdAt: new Date(),
  services: {
    password: {
      bcrypt: "$2b$10$n9CM8OgInDlwpvjLKLmAwe/ksAbjmmqFXnOgK2t6VlE2FiQXdpaXO"
    }
  },
  username: "admin",
  emails: [{address: "admin@rocket.gsi.srv.br", verified: true}],
  type: "user",
  status: "online",
  active: true,
  roles: ["admin"],
  name: "Administrador",
  __updatedAt: new Date()
});
print("ADMIN_CREATED");
' 2>&1""")
    print(f"   {out[:500]}")

# 4. Test login with new password
print("\n4. Testando login admin:")
time.sleep(2)
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://rocket.gsi.srv.br/api/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"Admin@1234"}'""")
try:
    resp = json.loads(out)
    if resp.get('status') == 'success':
        print(f"   ✓ Login OK!")
        print(f"   authToken: {resp['data']['authToken'][:30]}...")
        print(f"   userId: {resp['data']['userId']}")
    else:
        print(f"   ✗ Login falhou: {resp.get('message', resp.get('error', out[:200]))}")
        # Try with existing users
        print(f"\n   Tentando com outros usuarios...")
        out2, _, _ = ssh_exec("""docker exec mongo mongosh rocketchat --eval '
db.users.find({},{username:1,emails:1,roles:1}).limit(5).forEach(function(u){
  printjson({id:u._id, username:u.username, roles:u.roles, email:u.emails?u.emails[0]:null})
})
' 2>&1""")
        print(out2[:1000])
except:
    print(f"   Erro: {out[:300]}")

print("\n=== END ===")
