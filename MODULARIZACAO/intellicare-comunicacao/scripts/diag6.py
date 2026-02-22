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

print("=== PROSODY CONFIG GENERATION ANALYSIS ===\n")

JITSI_DIR = '/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb'

# 1. Check how Prosody generates its config (startup scripts)
print("1. PROSODY STARTUP SCRIPTS:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 ls -la /etc/cont-init.d/ 2>/dev/null || docker exec jitsi-meet-prosody-1 ls -la /etc/services.d/ 2>/dev/null")
print(out)

# 2. Check the config generation script
print("\n2. CONFIG GENERATION SCRIPT:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /etc/cont-init.d/10-config 2>/dev/null | head -100")
print(out[:4000])

# 3. Check if GLOBAL_CONFIG env var is supported
print("\n3. SEARCHING FOR cache_keys_url AND GLOBAL_CONFIG IN STARTUP:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /etc/cont-init.d/10-config 2>/dev/null | grep -n -i 'cache_keys\\|global_config\\|require_room\\|asap_key_server\\|ASAP_KEYSERVER\\|custom'")
print(f"   {out}")

# 4. Check the full Prosody config template
print("\n4. PROSODY CONFIG TEMPLATE:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /defaults/conf.d/jitsi-meet.cfg.lua 2>/dev/null | head -60")
print(out[:3000])

# 5. Check what custom config directories are available
print("\n5. CUSTOM CONFIG DIRS:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 ls -la /prosody-plugins-custom/ 2>/dev/null")
print(out if out.strip() else "   /prosody-plugins-custom/ not found or empty")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 ls -la /config/conf.d/ 2>/dev/null")
print(f"   /config/conf.d/: {out}")

# 6. Check the docker-compose volumes for prosody
print("\n6. PROSODY VOLUMES:")
out, err, rc = ssh_exec(f"grep -A30 'prosody:' {JITSI_DIR}/docker-compose-jitsi.yml | grep -A15 'volumes'")
print(f"   {out}")

# 7. Check the Prosody env vars
print("\n7. PROSODY ENV VARS (JWT related):")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 env 2>/dev/null | grep -i 'jwt\\|token\\|auth\\|asap\\|cache\\|global\\|custom' | sort")
print(f"   {out}")

# 8. Check if there's an override config mechanism
print("\n8. CONFIG OVERRIDE FILES:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find /config -name '*.cfg.lua' 2>/dev/null")
print(f"   {out}")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /config/conf.d/jitsi-meet.cfg.lua 2>/dev/null | tail -30")
print(f"   End of config:\n{out}")

print("\n=== END ===")
