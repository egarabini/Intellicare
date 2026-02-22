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

ENV_FILE = "/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/.env"
COMPOSE_DIR = "/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

print("=== FIX: ENABLE GUESTS FOR OAUTH FLOW ===\n")

# 1. Backup current .env
ts = int(time.time())
out, _, _ = ssh_exec(f"cp {ENV_FILE} {ENV_FILE}.backup.guests.{ts}")
print(f"1. Backup created: .env.backup.guests.{ts}")

# 2. Change ENABLE_GUESTS=0 to ENABLE_GUESTS=1
print("\n2. Enabling ENABLE_GUESTS=1:")
out, _, _ = ssh_exec(f"sed -i 's/^ENABLE_GUESTS=0/ENABLE_GUESTS=1/' {ENV_FILE}")
out, _, _ = ssh_exec(f"grep 'ENABLE_GUESTS' {ENV_FILE}")
print(f"   Current value: {out.strip()}")

# 3. Verify the XMPP_GUEST_DOMAIN is set
out, _, _ = ssh_exec(f"grep 'XMPP_GUEST_DOMAIN' {ENV_FILE}")
print(f"   Guest domain: {out.strip()}")

# 4. Restart containers
print("\n3. Restarting containers:")
out, err, rc = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml down 2>&1", timeout=60)
print(f"   Down: {out.strip()[-200:]}")
time.sleep(3)

out, err, rc = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml up -d 2>&1", timeout=120)
print(f"   Up: {out.strip()[-300:]}")
time.sleep(10)

# 5. Verify containers
print("\n4. Container status:")
out, _, _ = ssh_exec("docker ps --filter name=jitsi-meet --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 6. Check if guest VirtualHost was generated
print("\n5. Prosody config - VirtualHosts:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n 'VirtualHost\\|authentication\\|anonymous' /config/conf.d/jitsi-meet.cfg.lua 2>/dev/null")
print(out)

# 7. Check if config.js has anonymousdomain now
print("\n6. Config.js - anonymousdomain:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'anonymousdomain\\|guest\\|tokenAuth' /config/config.js 2>/dev/null")
print(out)

# 8. Check the full guest VirtualHost in Prosody config
print("\n7. Prosody guest VirtualHost details:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -A10 'guest' /config/conf.d/jitsi-meet.cfg.lua 2>/dev/null")
print(out)

# 9. Test auth URL
print("\n8. Auth URL test (from server):")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test123&state=teste' --max-time 10")
print(f"   Keycloak auth endpoint: HTTP {out}")

out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/teste' --max-time 10")
print(f"   Jitsi page: HTTP {out}")

out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   oauth.html: HTTP {out}")

# 10. Check Prosody logs after restart
print("\n9. Prosody logs (post-restart):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 15 2>&1 | grep -E 'error|warn|token|auth|guest' -i")
print(out if out.strip() else "   No relevant entries")

# 11. Check GLOBAL_CONFIG is still in prosody.cfg.lua
print("\n10. GLOBAL_CONFIG still present:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n 'cache_keys_url\\|asap_require_room_claim' /config/prosody.cfg.lua 2>/dev/null")
print(out if out.strip() else "   NOT FOUND - PROBLEM!")

print("\n=== DONE ===")
print("\nPlease test again: https://meet.gsi.srv.br/teste")
print("Expected flow:")
print("  1. Jitsi loads → connects as guest")
print("  2. Shows 'Login' button or auto-opens Keycloak popup")
print("  3. You login with: admin@saudeplanner.com.br / Test@1234")
print("  4. Keycloak redirects to oauth.html with token")
print("  5. Jitsi reconnects with JWT as authenticated moderator")
