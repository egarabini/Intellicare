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

print("=== JITSI AUTH FLOW INVESTIGATION ===\n")

# 1. Prosody logs - what happened when user tried "I am the host"
print("1. PROSODY LOGS (last 50 lines):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 50 2>&1")
print(out[:4000])

# 2. Check Jitsi JS files that handle the auth flow
print("\n2. JITSI AUTH JS FILES:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 find /usr/share/jitsi-meet -name '*.js' | head -20")
print(f"   JS files: {out}")

# 3. Search for tokenAuthUrl handling in Jitsi JS
print("\n3. SEARCH: tokenAuthUrl in JS files:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -r 'tokenAuthUrl\\|TOKEN_AUTH\\|oauthState\\|oauth\\.html\\|loginWindow\\|AuthHandler' /usr/share/jitsi-meet/libs/ 2>/dev/null | head -30")
print(out[:3000] if out.strip() else "   Not found in libs/")

# 4. Check lib-jitsi-meet or the main JS bundle for auth handling
print("\n4. MAIN BUNDLE - auth related:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 ls -la /usr/share/jitsi-meet/libs/ 2>/dev/null | head -20")
print(out)

# 5. Search for the auth/login popup mechanism
print("\n5. SEARCH in app.bundle.min.js for auth:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,100\\}tokenAuthUrl.\\{0,100\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -10")
print(out[:2000] if out.strip() else "   Not found")

# 6. Check for _location or window.open related to auth
print("\n6. SEARCH auth popup/open window:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,80\\}authUrl.\\{0,80\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -10")
print(out[:2000] if out.strip() else "   Not found")

# 7. Check for WaitForOwnerDialog or similar
print("\n7. SEARCH WaitForOwner/login dialog:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,100\\}WaitForOwner.\\{0,100\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -10")
print(out[:2000] if out.strip() else "   Not found in app.bundle")

out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,100\\}waitForOwner.\\{0,100\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -10")
print(out[:2000] if out.strip() else "   Not found (lowercase)")

# 8. Check for LOGIN_ENABLED or similar config
print("\n8. SEARCH login enable config:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,80\\}[Ll]ogin.\\{0,80\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -15")
print(out[:2000] if out.strip() else "   Not found")

# 9. Check the interface_config.js
print("\n9. INTERFACE_CONFIG.JS:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /usr/share/jitsi-meet/interface_config.js 2>/dev/null | grep -i 'auth\\|login\\|toolbar'")
print(out[:1000] if out.strip() else "   No auth settings")

# 10. Check if there's a TOOLBAR_BUTTONS setting hiding the login
print("\n10. CONFIG.JS - toolbar/login settings:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'toolbar\\|login\\|ENABLE_AUTH\\|securityUI\\|lobbyEnabled' /config/config.js 2>/dev/null")
print(out[:1000] if out.strip() else "   No relevant settings")

# 11. Get the actual Jitsi version used
print("\n11. JITSI VERSION:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /usr/share/jitsi-meet/manifest.json 2>/dev/null")
print(out[:500] if out.strip() else "   No manifest")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 head -5 /usr/share/jitsi-meet/base.html 2>/dev/null")
print(out[:300])

# 12. Check if Prosody's auth module sends the right error for "I am the host"
print("\n12. PROSODY MOD_AUTH_TOKEN - authentication flow:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n 'not-allowed\\|token required\\|401\\|403\\|password\\|authenticate' /usr/lib/prosody/modules/mod_saslauth.lua 2>/dev/null | head -10")
print(out[:500] if out.strip() else "   Not found")

print("\n=== END ===")
