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

print("=== FIX: Add cache_keys_url + asap_require_room_claim ===\n")

JITSI_DIR = '/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb'
CONFIG_DIR = '/root/.jitsi-meet-cfg'

# STEP 1: Backup .env
print("1. BACKUP .env:")
out, err, rc = ssh_exec(f"cp {JITSI_DIR}/.env {JITSI_DIR}/.env.backup.jwks.$(date +%s)")
print(f"   RC={rc}")

# STEP 2: Check if GLOBAL_CONFIG is already set
print("\n2. CURRENT GLOBAL_CONFIG:")
out, err, rc = ssh_exec(f"grep '^GLOBAL_CONFIG' {JITSI_DIR}/.env")
print(f"   [{out.strip()}]")

# STEP 3: Set GLOBAL_CONFIG with cache_keys_url and asap_require_room_claim
# The template uses splitList "\\n" which splits on literal \n characters
# So we put literal \n (two chars: backslash + n) between settings
GLOBAL_CONFIG_VALUE = 'cache_keys_url = "https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/certs"\\nasap_require_room_claim = false'

print(f"\n3. SETTING GLOBAL_CONFIG:")
print(f"   Value: {GLOBAL_CONFIG_VALUE}")

# Check if GLOBAL_CONFIG line exists and update it, or add it
out, err, rc = ssh_exec(f"grep -c '^GLOBAL_CONFIG' {JITSI_DIR}/.env")
count = out.strip()
if count == '0' or count == '':
    # Add it
    out, err, rc = ssh_exec(f"""echo 'GLOBAL_CONFIG={GLOBAL_CONFIG_VALUE}' >> {JITSI_DIR}/.env""")
    print(f"   Added new line. RC={rc}")
else:
    # Replace existing
    out, err, rc = ssh_exec(f"""sed -i 's|^GLOBAL_CONFIG=.*|GLOBAL_CONFIG={GLOBAL_CONFIG_VALUE}|' {JITSI_DIR}/.env""")
    print(f"   Updated existing line. RC={rc}")

# Verify
out, err, rc = ssh_exec(f"grep '^GLOBAL_CONFIG' {JITSI_DIR}/.env")
print(f"   Verify: [{out.strip()}]")

# STEP 4: Verify GLOBAL_CONFIG is passed to prosody in docker-compose
print("\n4. CHECK DOCKER-COMPOSE PROSODY ENV:")
out, err, rc = ssh_exec(f"grep -A50 'prosody:' {JITSI_DIR}/docker-compose-jitsi.yml | grep -E 'GLOBAL_CONFIG|JWT|AUTH|cache_keys'")
print(f"   {out}")

# STEP 5: Also check/verify the JWT env vars are passed to Prosody
print("\n5. VERIFY JWT ENV VARS IN DOCKER-COMPOSE:")
out, err, rc = ssh_exec(f"grep -A80 'prosody:' {JITSI_DIR}/docker-compose-jitsi.yml | grep -E 'JWT|ASAP'")
print(f"   {out}")

# If JWT vars aren't explicitly listed, check if env_file is used
if not out.strip():
    print("   JWT vars not found, checking for env_file:")
    out, err, rc = ssh_exec(f"grep -A5 'prosody:' {JITSI_DIR}/docker-compose-jitsi.yml | grep 'env_file'")
    print(f"   {out if out.strip() else '   No env_file found either'}")

# STEP 6: Restart ALL Jitsi containers (need full restart to regenerate configs)
print("\n6. RESTART ALL JITSI CONTAINERS:")
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -f docker-compose-jitsi.yml down 2>&1")
print(f"   Down: {out.strip()[:500]}")
time.sleep(3)
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -f docker-compose-jitsi.yml up -d 2>&1")
print(f"   Up: {out.strip()[:500]}")

# Wait for containers to start
print("   Waiting 15s for containers to start...")
time.sleep(15)

# STEP 7: Verify containers are running
print("\n7. CONTAINER STATUS:")
out, err, rc = ssh_exec("docker ps --filter 'name=jitsi' --format '{{.Names}} {{.Status}}'")
print(f"   {out}")

# STEP 8: Verify the generated Prosody config has GLOBAL_CONFIG settings
print("\n8. VERIFY PROSODY CONFIG - GLOBAL SETTINGS:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /config/prosody.cfg.lua 2>/dev/null | grep -n 'cache_keys_url\\|require_room_claim'")
print(f"   In prosody.cfg.lua: {out}")

print("\n9. VERIFY PROSODY CONFIG - FULL TAIL:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 tail -20 /config/prosody.cfg.lua 2>/dev/null")
print(f"   {out}")

# STEP 10: Check Prosody env vars
print("\n10. PROSODY ENV (GLOBAL_CONFIG):")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 env 2>/dev/null | grep GLOBAL_CONFIG")
print(f"   {out}")

# STEP 11: Test the auth flow
print("\n11. QUICK FUNCTIONAL TESTS:")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/teste' --max-time 10")
print(f"   meet.gsi.srv.br: HTTP {out}")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   oauth.html: HTTP {out}")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test12345&state=teste' --max-time 10")
print(f"   Keycloak auth: HTTP {out}")

# STEP 12: Check Prosody logs for any token errors
print("\n12. PROSODY RECENT LOGS:")
out, err, rc = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 20 2>&1 | grep -E '(error|warn|token|jwt|cache_keys|key_server)' -i")
print(f"   {out if out.strip() else '   No relevant log entries'}")

print("\n=== FIX APPLIED ===")
