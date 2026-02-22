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

print("=== PROSODY TOKEN VERIFICATION DEEP ANALYSIS ===\n")

# 1. Read the full luajwtjitsi library - this is the key JWT validation code
print("1. LUAJWTJITSI LIBRARY (full):")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 cat /prosody-plugins/luajwtjitsi.lib.lua 2>/dev/null")
print(out[:5000])

print("\n\n2. MOD_AUTH_TOKEN (how Prosody uses JWT):")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find / -path '*/mod_auth_token*' -o -path '*/mod_token*' 2>/dev/null | head -10")
print(f"   Files: {out}")
for f in out.strip().split('\n'):
    if f and f.endswith('.lua'):
        out2, err2, rc2 = ssh_exec(f"docker exec jitsi-meet-prosody-1 cat {f} 2>/dev/null | head -80")
        print(f"\n   === {f} ===\n{out2[:3000]}")

print("\n\n3. TOKEN_VERIFICATION MODULE:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find / -name 'token_verification*' 2>/dev/null | head -5")
print(f"   Files: {out}")
for f in out.strip().split('\n'):
    if f and f.endswith('.lua'):
        out2, err2, rc2 = ssh_exec(f"docker exec jitsi-meet-prosody-1 cat {f} 2>/dev/null")
        print(f"\n   === {f} ===\n{out2[:3000]}")

print("\n=== END ===")
