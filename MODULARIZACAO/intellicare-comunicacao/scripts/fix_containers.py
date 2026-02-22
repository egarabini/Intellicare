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

print("=== FIX: Container cleanup + verify config ===\n")

JITSI_DIR = '/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb'

# 1. Check for COMPOSE_PROJECT_NAME
print("1. COMPOSE_PROJECT_NAME in .env:")
out, err, rc = ssh_exec(f"grep COMPOSE_PROJECT_NAME {JITSI_DIR}/.env")
print(f"   [{out.strip()}]")

# 2. List ALL jitsi-related containers
print("\n2. ALL JITSI CONTAINERS:")
out, err, rc = ssh_exec("docker ps --format '{{.Names}} {{.Status}} {{.Image}}' | grep -i 'jitsi\\|meet\\|prosody\\|jicofo\\|jvb'")
print(f"   {out}")

# 3. Stop ALL jitsi containers (both old and new project names)
print("\n3. STOP ALL JITSI CONTAINERS:")
# Stop old project
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -p jitsi-meet -f docker-compose-jitsi.yml down 2>&1 | tail -5")
print(f"   Project 'jitsi-meet': {out.strip()}")
# Stop new project (directory-named)
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -f docker-compose-jitsi.yml down 2>&1 | tail -5")
print(f"   Default project: {out.strip()}")

time.sleep(3)

# 4. Verify no jitsi containers running
print("\n4. VERIFY NO JITSI CONTAINERS:")
out, err, rc = ssh_exec("docker ps --format '{{.Names}}' | grep -i 'jitsi\\|meet\\|prosody\\|jicofo\\|jvb'")
print(f"   Running: [{out.strip() if out.strip() else 'none - clean!'}]")

# Force kill any remaining
if out.strip():
    for name in out.strip().split('\n'):
        if name:
            ssh_exec(f"docker rm -f {name} 2>/dev/null")
    print("   Force removed remaining containers")

# 5. Set COMPOSE_PROJECT_NAME if not set
print("\n5. ENSURE COMPOSE_PROJECT_NAME:")
out, err, rc = ssh_exec(f"grep -c 'COMPOSE_PROJECT_NAME' {JITSI_DIR}/.env")
if out.strip() == '0':
    ssh_exec(f"echo 'COMPOSE_PROJECT_NAME=jitsi-meet' >> {JITSI_DIR}/.env")
    print("   Added COMPOSE_PROJECT_NAME=jitsi-meet")
else:
    print("   Already set")

# 6. Verify .env has all required settings
print("\n6. VERIFY .ENV KEY SETTINGS:")
out, err, rc = ssh_exec(f"grep -E '^(GLOBAL_CONFIG|COMPOSE_PROJECT|JWT_|AUTH_TYPE|ENABLE_AUTH|ENABLE_GUESTS|TOKEN_AUTH_URL)' {JITSI_DIR}/.env")
print(f"   {out}")

# 7. Start containers with explicit project name
print("\n7. START JITSI CONTAINERS:")
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -f docker-compose-jitsi.yml up -d 2>&1 | tail -10")
print(f"   {out}")

print("   Waiting 20s for all containers to start...")
time.sleep(20)

# 8. Verify containers
print("\n8. CONTAINER STATUS:")
out, err, rc = ssh_exec("docker ps --format '{{.Names}} {{.Status}}' | grep -i 'jitsi\\|meet\\|prosody\\|jicofo\\|jvb'")
print(f"   {out}")

# 9. Verify the CORRECT Prosody container has GLOBAL_CONFIG
print("\n9. PROSODY ENV (GLOBAL_CONFIG):")
# Find the prosody container
out, err, rc = ssh_exec("docker ps --format '{{.Names}}' | grep prosody | head -1")
prosody = out.strip()
print(f"   Container: {prosody}")
if prosody:
    out, err, rc = ssh_exec(f"docker exec {prosody} env 2>/dev/null | grep GLOBAL_CONFIG")
    print(f"   GLOBAL_CONFIG: [{out.strip()}]")

# 10. Verify prosody.cfg.lua has cache_keys_url
print("\n10. PROSODY CONFIG - cache_keys_url:")
if prosody:
    out, err, rc = ssh_exec(f"docker exec {prosody} grep -n 'cache_keys_url\\|require_room_claim' /config/prosody.cfg.lua 2>/dev/null")
    print(f"   {out}")

# 11. Verify jitsi-meet.cfg.lua - VirtualHost JWT settings
print("\n11. JITSI-MEET CONFIG - JWT SETTINGS:")
if prosody:
    out, err, rc = ssh_exec(f"docker exec {prosody} grep -n 'asap_key_server\\|cache_keys\\|require_room\\|app_id\\|app_secret\\|accepted_issuers\\|accepted_audiences\\|allow_empty\\|domain_verification\\|authentication.*token' /config/conf.d/jitsi-meet.cfg.lua 2>/dev/null")
    print(f"   {out}")

# 12. Verify token/jwk module exists (needed for JWKS → PEM conversion)
print("\n12. JWK MODULE:")
if prosody:
    out, err, rc = ssh_exec(f"docker exec {prosody} find / -name 'jwk*' 2>/dev/null | head -5")
    print(f"   {out}")

# 13. Quick functional tests
print("\n13. FUNCTIONAL TESTS:")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/teste' --max-time 10")
print(f"   meet.gsi.srv.br: HTTP {out}")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/config.js' --max-time 10")
print(f"   config.js: HTTP {out}")
out, err, rc = ssh_exec("curl -s -k 'https://meet.gsi.srv.br/config.js' --max-time 10 | grep tokenAuthUrl")
print(f"   tokenAuthUrl: [{out.strip()[:200]}]")

# 14. Check Prosody logs for cache_keys loading
print("\n14. PROSODY LOGS (startup):")
if prosody:
    out, err, rc = ssh_exec(f"docker logs {prosody} 2>&1 | tail -30")
    print(f"   {out}")

print("\n=== COMPLETE ===")
