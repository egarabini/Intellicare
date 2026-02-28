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

print("=== ROCKET CHAT - FIX MONGODB + RESTART ===\n")

# 1. Read the docker-compose-chat.yml
print("1. DOCKER-COMPOSE-CHAT.YML:")
out, _, _ = ssh_exec(f"cat {COMPOSE_DIR}/docker-compose-chat.yml")
print(out[:5000])

# 2. Check MongoDB replica set status
print("\n2. MONGODB REPLICASET STATUS:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.status()' 2>&1")
print(out[:3000])

# 3. Check MongoDB current hostname
print("\n3. MONGODB HOSTNAME ATUAL:")
out, _, _ = ssh_exec("docker exec mongo hostname 2>&1")
print(f"   Hostname: {out.strip()}")

# 4. Check the replica set config
print("\n4. REPLICASET CONFIG:")
out, _, _ = ssh_exec("docker exec mongo mongosh --eval 'rs.conf()' 2>&1")
print(out[:3000])

# 5. Check mongo-init-replica
print("\n5. MONGO-INIT-REPLICA:")
out, _, _ = ssh_exec("docker inspect mongo-init-replica 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin)[0]; print(d[\"Config\"][\"Cmd\"])' 2>/dev/null")
print(f"   CMD: {out.strip()}")
out, _, _ = ssh_exec("docker logs mongo-init-replica 2>&1 | tail -10")
print(f"   Logs: {out}")

print("\n=== END ===")
