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

print("=== TEMPLATE ANALYSIS ===\n")

# 1. Look at the template to find where asap_key_server, GLOBAL_CONFIG, and cache_keys_url are referenced
print("1. TEMPLATE - JWT and KEY related sections:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /defaults/conf.d/jitsi-meet.cfg.lua | grep -n -i 'asap_key_server\\|cache_keys\\|global_config\\|require_room\\|signatur'")
print(out)

# 2. Full template - look for overall structure with GLOBAL_CONFIG
print("\n2. MAIN PROSODY CFG TEMPLATE - GLOBAL_CONFIG:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /defaults/prosody.cfg.lua | grep -n -i 'global_config\\|GLOBAL'")
print(out)

# 3. Read the full main prosody.cfg.lua template
print("\n3. MAIN PROSODY TEMPLATE (full):")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /defaults/prosody.cfg.lua")
print(out[:3000])

# 4. Read the generated main config
print("\n4. GENERATED MAIN CONFIG:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /config/prosody.cfg.lua")
print(out[:2000])

# 5. Read the jitsi-meet template - specifically the JWT section
print("\n5. JITSI-MEET TEMPLATE - JWT SECTION:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /defaults/conf.d/jitsi-meet.cfg.lua | grep -n -B2 -A2 'asap_key\\|app_secret\\|require_room\\|cache_keys\\|JWT'")
print(out[:3000])

# 6. Find where exactly asap_key_server is set in the template  
print("\n6. TEMPLATE AROUND asap_key_server:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n 'asap_key' /defaults/conf.d/jitsi-meet.cfg.lua")
print(out)
# Get those lines with context
for line in out.strip().split('\n'):
    if line:
        num = line.split(':')[0]
        start = max(1, int(num) - 5)
        end_l = int(num) + 5
        out2, _, _ = ssh_exec(f"docker exec jitsi-meet-prosody-1 sed -n '{start},{end_l}p' /defaults/conf.d/jitsi-meet.cfg.lua")
        print(f"   Context around line {num}:\n{out2}")

# 7. Check GLOBAL_CONFIG in the jitsi-meet template
print("\n7. GLOBAL_CONFIG IN TEMPLATE:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n -i 'global' /defaults/conf.d/jitsi-meet.cfg.lua")
print(out if out.strip() else "   Not found in jitsi-meet template")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n -i 'global' /defaults/prosody.cfg.lua")
print(f"   In main template:\n{out}")

print("\n=== END ===")
