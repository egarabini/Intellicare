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

print("=== ROCKET CHAT - DIAGNOSTICO COMPLETO ===\n")

# 1. Container status
print("1. CONTAINERS ROCKET CHAT:")
out, _, _ = ssh_exec("docker ps -a --filter 'name=rocket\\|mongo' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}' 2>&1")
print(out)

# 2. Find docker-compose files for rocketchat
print("\n2. DOCKER-COMPOSE FILES:")
out, _, _ = ssh_exec("find /root -name 'docker-compose*' -path '*rocket*' 2>/dev/null; find /root -name 'docker-compose*' | xargs grep -l 'rocket' 2>/dev/null")
print(out if out.strip() else "   Nenhum arquivo especifico encontrado")

# Also check the main compose directory
out, _, _ = ssh_exec("find /root/install -name 'docker-compose*' 2>/dev/null | head -20")
print(f"\n   Todos os compose files:\n{out}")

# 3. Find Rocket Chat config/env
print("\n3. ROCKET CHAT ENV/CONFIG:")
out, _, _ = ssh_exec("docker inspect rocketchat 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; [print(e) for e in d[\"Config\"][\"Env\"] if any(k in e.upper() for k in [\"ROOT_URL\",\"MONGO\",\"PORT\",\"ADMIN\",\"OAUTH\",\"KEYCLOAK\",\"OIDC\",\"SAML\",\"LDAP\",\"URL\",\"DOMAIN\"])]' 2>/dev/null")
print(out if out.strip() else "   Nao encontrado via inspect")

# Full env
print("\n   ENV completo:")
out, _, _ = ssh_exec("docker inspect rocketchat 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; [print(e) for e in d[\"Config\"][\"Env\"]]' 2>/dev/null")
print(out[:3000] if out.strip() else "   Container nao encontrado")

# 4. Rocket Chat version and status
print("\n4. ROCKET CHAT VERSION/STATUS:")
out, _, _ = ssh_exec("docker logs rocketchat --tail 20 2>&1")
print(out[:3000] if out.strip() else "   Sem logs")

# 5. MongoDB status
print("\n5. MONGODB STATUS:")
out, _, _ = ssh_exec("docker ps -a --filter 'name=mongo' --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1")
print(out)
out, _, _ = ssh_exec("docker logs mongo --tail 10 2>&1; docker logs mongodb --tail 10 2>&1")
print(out[:2000] if out.strip() else "   Sem logs mongo")

# 6. Traefik labels for rocketchat
print("\n6. TRAEFIK LABELS (rocketchat):")
out, _, _ = ssh_exec("docker inspect rocketchat 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; labels=d[\"Config\"][\"Labels\"]; [print(f\"  {k}: {v}\") for k,v in sorted(labels.items()) if \"traefik\" in k.lower()]' 2>/dev/null")
print(out if out.strip() else "   Sem labels traefik")

# 7. Network config
print("\n7. NETWORK:")
out, _, _ = ssh_exec("docker inspect rocketchat 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; nets=d[\"NetworkSettings\"][\"Networks\"]; [print(f\"  {n}: {v.get(\"IPAddress\",\"\")} gateway={v.get(\"Gateway\",\"\")}\") for n,v in nets.items()]' 2>/dev/null")
print(out if out.strip() else "   Sem rede")

# 8. Check if rocketchat URL is accessible
print("\n8. ACESSIBILIDADE:")
# Try common URLs
for url in ['https://chat.gsi.srv.br', 'https://rocket.gsi.srv.br', 'https://rocketchat.gsi.srv.br', 'http://localhost:3000']:
    out, _, _ = ssh_exec(f"curl -s -k -o /dev/null -w '%{{http_code}}' '{url}' --max-time 5 2>/dev/null")
    print(f"   {url}: HTTP {out}")

# 9. Traefik routes
print("\n9. TRAEFIK ROUTES (todas):")
out, _, _ = ssh_exec("docker inspect traefik 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; ports=d[\"NetworkSettings\"][\"Ports\"]; print(ports.keys())' 2>/dev/null")
out, _, _ = ssh_exec("curl -s -k 'https://localhost:8080/api/http/routers' 2>/dev/null | python3 -c 'import sys,json; routers=json.load(sys.stdin); [print(f\"  {r[\"name\"]}: {r.get(\"rule\",\"\")} -> {r.get(\"service\",\"\")}\") for r in routers]' 2>/dev/null")
print(out if out.strip() else "   Traefik API nao acessivel, tentando alternativa...")
if not out.strip():
    out, _, _ = ssh_exec("docker exec traefik cat /etc/traefik/traefik.yml 2>/dev/null | head -30")
    print(out[:1000])

# 10. Find the actual docker-compose that runs rocketchat 
print("\n10. COMPOSE FILE COM ROCKETCHAT:")
out, _, _ = ssh_exec("docker inspect rocketchat 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; labels=d[\"Config\"][\"Labels\"]; [print(f\"  {k}: {v}\") for k,v in labels.items() if \"compose\" in k.lower()]' 2>/dev/null")
print(out if out.strip() else "   Sem labels compose")

# 11. Keycloak - existe client para rocketchat?
print("\n11. KEYCLOAK - CLIENTS EXISTENTES:")
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=egarabini%40gmail.com&password=Crazy%2357LB&grant_type=password&client_id=admin-cli'""")
try:
    admin_token = json.loads(out)['access_token']
    out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients?first=0&max=50'")
    clients = json.loads(out)
    print(f"   Total clients: {len(clients)}")
    for c in clients:
        cid = c.get('clientId', '')
        if not cid.startswith('account') and not cid.startswith('broker') and not cid.startswith('realm') and not cid.startswith('security') and not cid.startswith('admin'):
            print(f"   - {cid} (enabled={c.get('enabled')}, public={c.get('publicClient')})")
except Exception as e:
    print(f"   Erro: {e}")

print("\n=== END ===")
