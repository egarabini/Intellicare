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

print("=== ROCKET CHAT - WAIT + CHECK ===\n")

# The compose recreated mongo too (new container), need to re-init replica set
print("1. Re-init replica set (container novo):")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.status()' 2>&1")
if 'Our replica set config is invalid' in out or 'no replset config' in out.lower():
    print("   Replica set precisa re-inicializar...")
    out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.initiate({_id:\"rs0\",members:[{_id:0,host:\"localhost:27017\"}]})' 2>&1")
    print(f"   Init: {out[:500]}")
    time.sleep(5)
else:
    print(f"   Status: {out[:500]}")

# Check replicaset
print("\n2. Replica set status:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.status().members.forEach(function(m){printjson({name:m.name,state:m.stateStr,health:m.health})})' 2>&1")
print(out[:500])

# Wait for Rocket Chat to fully start
print("\n3. Esperando Rocket Chat iniciar (ate 60s)...")
for i in range(12):
    time.sleep(5)
    out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://rocket.gsi.srv.br' --max-time 5 2>/dev/null")
    status = out.strip()
    print(f"   {(i+1)*5}s: HTTP {status}")
    if status == '200':
        break

# 4. Container status
print("\n4. Status containers:")
out, _, _ = ssh_exec("docker ps --filter 'name=rocket\\|mongo' --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 5. Logs
print("\n5. Rocket Chat logs (ultimas 40 linhas):")
out, _, _ = ssh_exec("docker logs rocketchat --tail 40 2>&1")
print(out[:4000])

# 6. MongoDB health
print("\n6. MongoDB logs (ultimas 5 linhas):")
out, _, _ = ssh_exec("docker logs mongo --tail 5 2>&1")
print(out[:1000])

print("\n=== END ===")
