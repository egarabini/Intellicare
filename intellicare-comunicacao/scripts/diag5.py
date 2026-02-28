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

print("=== TOKEN/UTIL.LUA - Core token validation ===\n")

# 1. Find token/util.lua
print("1. FIND token/util.lua:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find / -path '*/token/util*' 2>/dev/null | head -10")
print(f"   {out}")

for f in out.strip().split('\n'):
    if f and f.endswith('.lua'):
        print(f"\n=== {f} ===")
        out2, err2, rc2 = ssh_exec(f"docker exec jitsi-meet-prosody-1 cat {f}")
        print(out2)
        break

print("\n=== END ===")
