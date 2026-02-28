import paramiko

def ssh_exec(cmd, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('161.97.141.186', port=22, username='root', password='Crazy57LB', timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    ssh.close()
    return out, err

# 1. Docker containers running
print('=== DOCKER CONTAINERS ===')
out, err = ssh_exec('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -30')
print(out)

# 2. Jitsi specific containers
print('=== JITSI CONTAINERS ===')
out, err = ssh_exec('docker ps -a --filter name=jitsi --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')
print(out)

# 3. Directory listing
print('=== JITSI DIR ===')
out, err = ssh_exec('ls -la /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/')
print(out)
