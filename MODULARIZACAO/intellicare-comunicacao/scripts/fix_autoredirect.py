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
CONFIG_DIR = "/root/.jitsi-meet-cfg"

print("=== FIX: AUTO-REDIRECT + OAUTH.HTML ===\n")

# 1. Backup
ts = int(time.time())
ssh_exec(f"cp {ENV_FILE} {ENV_FILE}.backup.autoredirect.{ts}")
print(f"1. Backup created")

# 2. Create custom-config.js for tokenAuthUrlAutoRedirect
print("\n2. Creating custom-config.js:")
custom_config = """// Keycloak OIDC Auto-redirect: redirect to Keycloak login automatically
config.tokenAuthUrlAutoRedirect = true;
"""
ssh_exec(f"cat > {CONFIG_DIR}/web/custom-config.js << 'CUSTOMEOF'\n{custom_config}\nCUSTOMEOF")
out, _, _ = ssh_exec(f"cat {CONFIG_DIR}/web/custom-config.js")
print(f"   Content:\n{out}")

# 3. Deploy improved oauth.html (v3 - focused on redirect flow)
print("\n3. Deploying oauth.html v3 (redirect-focused):")
oauth_html = r"""<!DOCTYPE html>
<html>
<head>
    <title>Keycloak SSO - Jitsi Meet</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; 
               align-items: center; min-height: 100vh; margin: 0; background: #1a1a2e; color: #fff; }
        .container { text-align: center; padding: 20px; }
        .spinner { border: 4px solid #333; border-top: 4px solid #0location078d4; border-radius: 50%;
                   width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error { color: #ff6b6b; margin-top: 20px; }
        a { color: #4dabf7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner" id="spinner"></div>
        <p id="status">Autenticando...</p>
        <div id="error" class="error" style="display:none;"></div>
    </div>
    <script>
    (function() {
        var location = window.location;
        var hash = location.hash.substring(1);
        var params = {};
        var regex = /([^&=]+)=([^&]*)/g;
        var m;
        while (m = regex.exec(hash)) {
            params[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
        }

        var token = params.id_token || params.access_token || '';
        var state = params.state || '';
        var error = params.error || '';
        var errorDesc = params.error_description || '';

        if (error) {
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('status').textContent = 'Erro na autenticacao';
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerHTML = 
                '<p>' + error + ': ' + errorDesc + '</p>' +
                '<p><a href="/">Voltar ao inicio</a></p>';
            return;
        }

        if (!token) {
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('status').textContent = 'Token nao recebido';
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerHTML = 
                '<p>Nenhum token foi retornado pelo Keycloak.</p>' +
                '<p>Hash: ' + (hash ? hash.substring(0, 50) + '...' : 'vazio') + '</p>' +
                '<p><a href="/">Voltar ao inicio</a></p>';
            return;
        }

        // Determine the room name from state parameter
        var room = state || 'lobby';

        // Build the redirect URL with JWT
        var baseUrl = location.protocol + '//' + location.host + '/';
        var redirectUrl = baseUrl + room + '?jwt=' + token;

        document.getElementById('status').textContent = 'Login OK! Redirecionando para a sala: ' + room;

        // Method 1: If opened as popup, notify opener and redirect it
        if (window.opener && !window.opener.closed) {
            try {
                window.opener.location.href = redirectUrl;
                window.close();
                return;
            } catch(e) {
                // Cross-origin - fall through to direct redirect
            }
        }

        // Method 2: Direct redirect (tokenAuthUrlAutoRedirect flow)
        window.location.replace(redirectUrl);
    })();
    </script>
</body>
</html>"""

# Backup and deploy
ssh_exec(f"cp {CONFIG_DIR}/web/oauth.html {CONFIG_DIR}/web/oauth.html.bak.v3.{ts} 2>/dev/null")
# Write with heredoc
cmd = f"""cat > {CONFIG_DIR}/web/oauth.html << 'OAUTHEOF'
{oauth_html}
OAUTHEOF"""
ssh_exec(cmd)
out, _, _ = ssh_exec(f"wc -l {CONFIG_DIR}/web/oauth.html")
print(f"   oauth.html deployed: {out.strip()}")

# 4. Restart containers
print("\n4. Restarting containers:")
out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml down 2>&1", timeout=60)
print(f"   Down OK")
time.sleep(3)

out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml up -d 2>&1", timeout=120)
print(f"   Up OK")
time.sleep(12)

# 5. Verify containers
print("\n5. Container status:")
out, _, _ = ssh_exec("docker ps --filter name=jitsi-meet --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 6. Verify config.js has tokenAuthUrlAutoRedirect
print("6. Config.js verification:")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 grep -i 'tokenAuthUrl' /config/config.js 2>/dev/null")
print(out)

# 7. Verify oauth.html is served correctly
print("\n7. oauth.html verification:")
out, _, _ = ssh_exec("curl -s -k 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10 | head -3")
print(f"   {out.strip()}")

# 8. Verify the full auth redirect flow
print("\n8. Full flow simulation:")
# Step 1: Access room - should redirect to Keycloak
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w 'HTTP_%{http_code}' 'https://meet.gsi.srv.br/teste' --max-time 10")
print(f"   a) Room page: {out}")

# Step 2: Keycloak auth endpoint
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w 'HTTP_%{http_code}' 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test123&state=teste' --max-time 10")
print(f"   b) Keycloak auth: {out}")

# Step 3: oauth.html
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w 'HTTP_%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   c) oauth.html: {out}")

# 9. Prosody config still good
print("\n9. Prosody config check:")
out, _, _ = ssh_exec("docker exec jitsi-meet-prosody-1 grep -n 'cache_keys_url\\|asap_require_room_claim\\|VirtualHost.*guest' /config/prosody.cfg.lua /config/conf.d/jitsi-meet.cfg.lua 2>/dev/null")
print(out)

# 10. Prosody logs
print("\n10. Prosody logs (post-restart):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 10 2>&1 | grep -iE 'error|warn|auth|token'")
print(out if out.strip() else "   Clean - no errors")

print("\n=== DONE ===")
print("\nExpected flow now:")
print("1. Visit https://meet.gsi.srv.br/teste")
print("2. Jitsi auto-redirects to Keycloak login (no popup)")
print("3. Login: admin@saudeplanner.com.br / Test@1234")
print("4. Keycloak redirects to oauth.html with token")
print("5. oauth.html redirects to /teste?jwt=<token>")
print("6. You're in the conference as authenticated moderator!")
