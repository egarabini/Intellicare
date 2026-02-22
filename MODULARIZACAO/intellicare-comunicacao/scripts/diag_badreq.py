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

print("=== BAD REQUEST DIAGNOSIS ===\n")

# 1. Recent Keycloak logs (errors)
print("1. KEYCLOAK LOGS (last 50 lines, errors):")
out, _, _ = ssh_exec("docker logs keycloak --tail 50 2>&1 | grep -i 'error\\|warn\\|bad\\|invalid\\|client_id\\|redirect\\|WARN'")
print(out if out.strip() else "   No errors found")

print("\n2. KEYCLOAK LOGS (last 30 lines, ALL):")
out, _, _ = ssh_exec("docker logs keycloak --tail 30 2>&1")
print(out[:3000])

# 2. Prosody logs
print("\n3. PROSODY LOGS (last 30 lines):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 30 2>&1")
print(out[:3000])

# 3. Web/Jitsi logs
print("\n4. JITSI WEB LOGS (last 20 lines):")
out, _, _ = ssh_exec("docker logs jitsi-meet-web-1 --tail 20 2>&1")
print(out[:2000])

# 4. Check the current TOKEN_AUTH_URL in config.js
print("\n5. TOKEN_AUTH_URL in config.js:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'tokenAuthUrl\\|TOKEN_AUTH' /config/config.js 2>/dev/null")
print(out if out.strip() else "   Not found in config.js")

# 5. Check the Keycloak client settings again
print("\n6. KEYCLOAK CLIENT 'jitsi-meet' DETAILS:")
# Get admin token
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=egarabini%40gmail.com&password=Crazy%2357LB&grant_type=password&client_id=admin-cli'""")
try:
    admin_token = json.loads(out)['access_token']
    
    # Get client ID
    out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/clients?clientId=jitsi-meet'")
    clients = json.loads(out)
    if clients:
        client = clients[0]
        cid = client['id']
        print(f"   clientId: {client.get('clientId')}")
        print(f"   enabled: {client.get('enabled')}")
        print(f"   publicClient: {client.get('publicClient')}")
        print(f"   implicitFlowEnabled: {client.get('implicitFlowEnabled')}")
        print(f"   standardFlowEnabled: {client.get('standardFlowEnabled')}")
        print(f"   directAccessGrantsEnabled: {client.get('directAccessGrantsEnabled')}")
        print(f"   redirectUris: {client.get('redirectUris')}")
        print(f"   webOrigins: {client.get('webOrigins')}")
        print(f"   rootUrl: {client.get('rootUrl')}")
        print(f"   baseUrl: {client.get('baseUrl')}")
        print(f"   protocol: {client.get('protocol')}")
        
        # Check valid redirect URIs more precisely
        print(f"\n   Full redirect URIs: {json.dumps(client.get('redirectUris', []))}")
except Exception as e:
    print(f"   Error: {e}")

# 6. Test the exact auth URL that Jitsi uses
print("\n7. SIMULATE AUTH URL (what browser sends):")
auth_url = "https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test123abc&state=teste"
out, _, _ = ssh_exec(f"curl -s -k -o /dev/null -w 'HTTP_%{{http_code}}\\nRedirect: %{{redirect_url}}' '{auth_url}' --max-time 10")
print(f"   {out}")

# Also get the response body if it's an error
out, _, _ = ssh_exec(f"curl -s -k '{auth_url}' --max-time 10 | head -30")
if 'error' in out.lower() or 'bad' in out.lower() or 'invalid' in out.lower():
    print(f"   RESPONSE BODY (contains error):\n{out[:2000]}")
else:
    print(f"   Response is HTML login page (OK)")

# 7. Check if the redirect_uri is exactly right
print("\n8. CHECK oauth.html ACCESSIBILITY:")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   https://meet.gsi.srv.br/static/oauth.html -> HTTP {out}")

# Also check without /static/
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/oauth.html' --max-time 10")
print(f"   https://meet.gsi.srv.br/oauth.html -> HTTP {out}")

# 8. Check what the .env TOKEN_AUTH_URL is actually set to
print("\n9. .ENV TOKEN_AUTH_URL:")
out, _, _ = ssh_exec("grep TOKEN_AUTH_URL /root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/.env")
print(f"   {out.strip()}")

# 9. Check Traefik logs for the request
print("\n10. TRAEFIK LOGS (last 10 lines for keycloak):")
out, _, _ = ssh_exec("docker logs traefik --tail 50 2>&1 | grep -i keycloak | tail -10")
print(out if out.strip() else "   No keycloak entries")

print("\n=== END ===")
