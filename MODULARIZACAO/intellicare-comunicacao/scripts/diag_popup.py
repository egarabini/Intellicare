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

print("=== POPUP & AUTH DEEP ANALYSIS ===\n")

# 1. Latest Prosody logs (after user's test)
print("1. PROSODY LOGS (latest 20 lines, ALL):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 20 2>&1")
print(out[:3000])

# 2. Search for window.open in the auth context
print("\n2. SEARCH window.open in app.bundle:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,150\\}window\\.open.\\{0,150\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | grep -i 'auth\\|token\\|login\\|oauth' | head -5")
print(out[:2000] if out.strip() else "   No auth-related window.open found")

# 3. Search more broadly for window.open
print("\n3. ALL window.open calls:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,80\\}window\\.open.\\{0,80\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -10")
print(out[:2000] if out.strip() else "   No window.open found")

# 4. Check how the login popup works - search for _onIAmHost
print("\n4. _onIAmHost handler:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,200\\}_onIAmHost.\\{0,200\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -5")
print(out[:2000] if out.strip() else "   Not found")

# 5. Search for the J5 function (login action from WaitForOwner)
print("\n5. Login/auth dispatch from WaitForOwner:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,200\\}openLoginDialog\\|openAuthDialog\\|showLoginDialog.\\{0,200\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -5")
print(out[:2000] if out.strip() else "   Not found")

# 6. Check the tokenAuthUrlAutoRedirect config option
print("\n6. tokenAuthUrlAutoRedirect in bundle:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -o '.\\{0,200\\}tokenAuthUrlAutoRedirect.\\{0,200\\}' /usr/share/jitsi-meet/libs/app.bundle.min.js 2>/dev/null | head -5")
print(out[:2000] if out.strip() else "   Not found")

# 7. Check the web config template for tokenAuthUrlAutoRedirect
print("\n7. WEB CONFIG TEMPLATE - tokenAuthUrlAutoRedirect:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'tokenAuthUrlAutoRedirect\\|AUTO_REDIRECT\\|auto_redirect' /defaults/config.js 2>/dev/null")
print(out if out.strip() else "   Not in template - need to add via custom config")

# 8. Check if there's a custom-config.js mechanism
print("\n8. Custom config mechanism:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 ls -la /config/ 2>/dev/null")
print(out[:1000])
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /defaults/config.js 2>/dev/null | grep -i 'custom\\|include\\|import' | head -5")
print(out[:500] if out.strip() else "   No custom config imports")

# 9. Check the web config template for CUSTOM CONFIG env var
print("\n9. Web config template support for env overrides:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'CUSTOM\\|EXTRA\\|TOKEN_AUTH_URL_AUTO\\|ENABLE_TOKEN' /defaults/config.js 2>/dev/null | head -10")
print(out[:500] if out.strip() else "   No relevant env vars found")

# 10. Check 10-config script for config generation
print("\n10. Config generation script (custom config support):")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /etc/cont-init.d/10-config 2>/dev/null | grep -i 'custom\\|append\\|extra\\|override' | head -10")
print(out[:500] if out.strip() else "   No custom config support in init script")

# 11. Check if custom-config.js is auto-loaded
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -r 'custom' /etc/cont-init.d/ 2>/dev/null | head -10")
print(out[:500] if out.strip() else "   No custom config in init")

# 12. Check the nginx config for config loading
print("\n11. NGINX CONFIG (how config.js is served):")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /defaults/meet.conf 2>/dev/null | grep -i 'config\\|ssi\\|include' | head -10")
print(out[:500] if out.strip() else "   Not found")

# 13. Check what our custom oauth.html currently contains
print("\n12. CURRENT oauth.html content:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 cat /usr/share/jitsi-meet/static/oauth.html 2>/dev/null")
print(out[:3000])

print("\n=== END ===")
