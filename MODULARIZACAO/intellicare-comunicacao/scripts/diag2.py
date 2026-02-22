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

JITSI_DIR = '/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb'

# 1. List jitsi dir
print('=== JITSI DIR ===')
out, err = ssh_exec(f'ls -la {JITSI_DIR}')
print(out)
if err: print('ERR:', err)

# 2. Docker compose file
print('=== DOCKER-COMPOSE-JITSI.YML ===')
out, err = ssh_exec(f'cat {JITSI_DIR}/docker-compose-jitsi.yml')
print(out)

# 3. .env file
print('=== .ENV FILE ===')
out, err = ssh_exec(f'cat {JITSI_DIR}/.env 2>/dev/null || echo "No .env file"')
print(out)

# 4. env file (alternative)
print('=== ENV FILE (alt) ===')
out, err = ssh_exec(f'cat {JITSI_DIR}/env 2>/dev/null || echo "No env file"')
print(out)
