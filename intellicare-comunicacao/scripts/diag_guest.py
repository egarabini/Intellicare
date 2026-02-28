import paramiko
import json

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

print("=== GUEST/AUTH FLOW DEEP ANALYSIS ===\n")

# 1. Full prosody.cfg.lua - check if guest VirtualHost exists
print("1. PROSODY CONFIG - ALL VirtualHosts:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 cat /config/prosody.cfg.lua | grep -n 'VirtualHost\\|authentication\\|anonymous\\|guest\\|allow_empty_token\\|token_auth\\|app_id'")
print(out)

# 2. Full jitsi-meet.cfg.lua  
print("\n2. JITSI-MEET CONFIG (conf.d):")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 cat /config/conf.d/jitsi-meet.cfg.lua")
print(out[:5000])

# 3. Check ENABLE_GUESTS and related env vars
print("\n3. ENV VARS (guest-related):")
out, _, _ = ssh_exec("grep -E 'ENABLE_GUESTS|ENABLE_AUTH|AUTH_TYPE|TOKEN_AUTH|XMPP_GUEST|XMPP_DOMAIN|XMPP_MUC|JWT_' /root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/.env")
print(out)

# 4. Check what config.js says about guests
print("\n4. CONFIG.JS (full relevant sections):")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /config/config.js")
print(out[:5000])

# 5. Check Prosody template for guest handling
print("\n5. PROSODY TEMPLATE - guest section:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n -A5 -B2 'guest\\|ENABLE_GUESTS\\|anonymous' /defaults/prosody.cfg.lua 2>/dev/null | head -50")
print(out)

# 6. Check web template for guest handling  
print("\n6. WEB CONFIG TEMPLATE - guest section:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -n -A3 -B2 'guest\\|ENABLE_GUESTS\\|anonymousdomain\\|tokenAuthUrl' /defaults/config.js 2>/dev/null | head -40")
print(out)

# 7. Check what HTML the user actually sees (the Jitsi page)
print("\n7. JITSI PAGE HTML (what user sees at /teste):")
out, _, _ = ssh_exec("curl -s -k 'https://meet.gsi.srv.br/teste' --max-time 10 | grep -i 'title\\|error\\|bad\\|request\\|auth\\|login'")
print(out if out.strip() else "   No error/auth text in HTML")

# 8. Docker-compose env section for web
print("\n8. DOCKER-COMPOSE WEB ENV:")
out, _, _ = ssh_exec("grep -A30 'services:' /root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/docker-compose-jitsi.yml | head -50")
print(out)

print("\n=== END ===")
