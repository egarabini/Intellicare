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

print("=== FIX MONGODB REPLICASET ===\n")

# 1. Fix replica set by reconfiguring to use "mongo" (service name) or "localhost"
print("1. Reconfigurando replica set para usar 'localhost:27017':")
# Use force=true to override invalid config
cmd = """docker exec mongo mongosh --eval '
var cfg = rs.conf();
cfg.members[0].host = "localhost:27017";
rs.reconfig(cfg, {force: true});
' 2>&1"""
out, _, _ = ssh_exec(cmd)
print(out[:2000])

time.sleep(3)

# 2. Check status after reconfig
print("\n2. Replica set status apos reconfig:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.status().members.forEach(function(m){printjson({name:m.name, state:m.stateStr, health:m.health})})' 2>&1")
print(out[:1000])

# 3. Verify MongoDB health
print("\n3. MongoDB health check:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'db.adminCommand({ping:1})' 2>&1")
print(out[:500])

# 4. Test writing to the database
print("\n4. Teste de escrita:")
out, _, _ = ssh_exec("docker exec mongo mongosh rocketchat --eval 'db.test_connection.insertOne({test: true, time: new Date()})' 2>&1")
print(out[:500])

# 5. Now restart Rocket Chat
print("\n5. Reiniciando Rocket Chat:")
out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-chat.yml up -d rocketchat 2>&1", timeout=60)
print(out[:1000])

time.sleep(15)

# 6. Check Rocket Chat status
print("\n6. Status Rocket Chat:")
out, _, _ = ssh_exec("docker ps --filter name=rocketchat --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 7. Rocket Chat logs
print("\n7. Rocket Chat logs (ultimas 30 linhas):")
out, _, _ = ssh_exec("docker logs rocketchat --tail 30 2>&1")
print(out[:3000])

# 8. MongoDB container health
print("\n8. MongoDB health:")
out, _, _ = ssh_exec("docker ps --filter name=mongo --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 9. Test URL
print("\n9. Teste de acesso:")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br' --max-time 10 2>/dev/null")
print(f"   https://rocket.gsi.srv.br: HTTP {out}")

print("\n=== END ===")
