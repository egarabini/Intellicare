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

print("=== FIX: MONGODB REPLICASET HOST = 'mongo:27017' ===\n")

# 1. Reconfigure replica set to use 'mongo:27017' (Docker service name)
print("1. Reconfigurando replica set para 'mongo:27017':")
cmd = """docker exec mongo mongosh --eval '
var cfg = rs.conf();
cfg.members[0].host = "mongo:27017";
rs.reconfig(cfg, {force: true});
print("OK: Reconfigurado para mongo:27017");
' 2>&1"""
out, _, _ = ssh_exec(cmd)
print(out[:1000])

time.sleep(3)

# 2. Verify
print("\n2. Verificando replica set:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.status().members.forEach(function(m){printjson({name:m.name,state:m.stateStr,health:m.health})})' 2>&1")
print(out[:500])

# 3. Test write
print("\n3. Teste de escrita no MongoDB:")
out, _, _ = ssh_exec("docker exec mongo mongosh rocketchat --eval 'db.test_ping.insertOne({ok:1,ts:new Date()})' 2>&1")
print(out[:300])

# 4. Restart Rocket Chat
print("\n4. Reiniciando Rocket Chat:")
out, _, _ = ssh_exec("docker restart rocketchat 2>&1")
print(f"   {out.strip()}")

# 5. Wait for startup (RC takes 30-60s)
print("\n5. Esperando Rocket Chat iniciar...")
for i in range(24):
    time.sleep(5)
    out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br' --max-time 5 2>/dev/null")
    status = out.strip()
    
    # Also check if container is still running
    out2, _, _ = ssh_exec("docker ps --filter name=rocketchat --format '{{.Status}}' 2>/dev/null")
    container_status = out2.strip()
    
    print(f"   {(i+1)*5}s: HTTP {status} | Container: {container_status}")
    
    if status == '200':
        print("   ✓ ROCKET CHAT ONLINE!")
        break
    
    if not container_status or 'Exited' in container_status:
        print("   ✗ Container parou! Verificando logs...")
        out3, _, _ = ssh_exec("docker logs rocketchat --tail 20 2>&1")
        print(out3[:2000])
        
        # Try restarting
        if 'Topology' in out3 or 'ECONNREFUSED' in out3:
            print("\n   Tentando restart...")
            ssh_exec("docker restart rocketchat 2>&1")
            continue
        break

# 6. Final status
print("\n6. Status final:")
out, _, _ = ssh_exec("docker ps --filter 'name=rocket\\|mongo' --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 7. Final logs
print("\n7. Rocket Chat logs (ultimas 15 linhas):")
out, _, _ = ssh_exec("docker logs rocketchat --tail 15 2>&1")
print(out[:2000])

print("\n=== END ===")
