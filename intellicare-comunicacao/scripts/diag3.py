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
<head>
    <meta charset="utf-8">
    <title>Jitsi Meet - Auth</title>
</head>
<body>
<script>
(function() {
    // Parse hash fragment from Keycloak implicit flow response
    // URL will be like: oauth.html#id_token=xxx&state=roomname&session_state=yyy
    var hash = window.location.hash.substring(1);
    var params = {};
    if (hash) {
        hash.split('&').forEach(function(pair) {
            var idx = pair.indexOf('=');
            if (idx > 0) {
                params[decodeURIComponent(pair.substring(0, idx))] = decodeURIComponent(pair.substring(idx + 1));
            }
        });
    }

    var token = params['id_token'] || params['access_token'];
    var state = params['state'] || '';
    var error = params['error'];
    var errorDesc = params['error_description'];

    if (token) {
        // SUCCESS: Got a token from Keycloak

        // Method 1: If opened as popup by Jitsi, send token back via postMessage
        if (window.opener) {
            try {
                // Send in Jitsi's expected format
                window.opener.postMessage({
                    oauthState: state,
                    oauthAccessToken: token,
                    oauthToken: token,
                    oauthType: 'keycloak',
                    type: 'location.hash',
                    location: window.location.href
                }, window.location.origin);

                // Also try the native Jitsi callback handler pattern
                if (typeof window.opener.location !== 'undefined') {
                    try {
                        // Redirect the opener to the room with JWT
                        window.opener.location.href = window.location.protocol + '//' + window.location.host + '/' + state + '?jwt=' + encodeURIComponent(token);
                    } catch(crossOriginError) {
                        // Cross-origin, postMessage already sent
                    }
                }

                setTimeout(function() { window.close(); }, 500);
                return;
            } catch(e) {
                // Fall through to redirect
            }
        }

        // Method 2: Direct redirect (if not in popup, or popup fallback)
        var baseUrl = window.location.protocol + '//' + window.location.host;
        var room = state || '';
        window.location.href = baseUrl + '/' + room + '?jwt=' + encodeURIComponent(token);

    } else if (error) {
        document.body.innerHTML = '<div style="text-align:center;margin-top:20%;font-family:Arial;color:#333;">' +
            '<h2>Erro de Autenticacao</h2>' +
            '<p><strong>' + error + '</strong></p>' +
            '<p>' + (errorDesc || '') + '</p>' +
            '<p><a href="javascript:window.close()">Fechar</a></p></div>';
    } else {
        document.body.innerHTML = '<div style="text-align:center;margin-top:20%;font-family:Arial;color:#333;">' +
            '<h2>Processando...</h2>' +
            '<p>Nenhum token recebido.</p>' +
            '<pre style="font-size:10px;text-align:left;max-width:600px;margin:auto;overflow:auto;">' +
            'URL: ' + window.location.href.substring(0, 200) + '\n' +
            'Hash: ' + window.location.hash.substring(0, 200) + '</pre></div>';
    }
})();
</script>
</body>
</html>'''

print("1. BACKUP current oauth.html:")
out, err, rc = ssh_exec(f"cp {CONFIG_DIR}/web/oauth.html {CONFIG_DIR}/web/oauth.html.bak.v2 2>/dev/null && echo 'backed up' || echo 'no file to backup'")
print(f"   {out.strip()}")

print("\n2. DEPLOY new oauth.html:")
# Escape for shell
escaped_html = NEW_OAUTH.replace("'", "'\\''")
out, err, rc = ssh_exec(f"cat > {CONFIG_DIR}/web/oauth.html << 'OAUTHEOF'\n{NEW_OAUTH}\nOAUTHEOF")
print(f"   Written. RC={rc}")
if err.strip():
    print(f"   Stderr: {err.strip()}")

# Verify
out, err, rc = ssh_exec(f"wc -l {CONFIG_DIR}/web/oauth.html && head -3 {CONFIG_DIR}/web/oauth.html")
print(f"   Verification: {out.strip()}")

print("\n3. VERIFY oauth.html is mounted in container:")
out, err, rc = ssh_exec("docker exec jitsi-meet-web-1 cat /usr/share/jitsi-meet/static/oauth.html 2>/dev/null | head -5")
print(f"   Container version:\n{out}")

# Since the file is mounted as a volume, changes should be reflected immediately
# But let's restart web container to be safe
print("\n4. RESTART web container:")
out, err, rc = ssh_exec(f"cd {JITSI_DIR} && docker compose -f docker-compose-jitsi.yml restart web 2>&1")
print(f"   {out.strip()}")

time.sleep(5)

print("\n5. VERIFY new oauth.html after restart:")
out, err, rc = ssh_exec("docker exec jitsi-meet-web-1 cat /usr/share/jitsi-meet/static/oauth.html 2>/dev/null | head -10")
print(f"   {out}")

# 6. Test the auth URL directly (should show Keycloak login page)
print("\n6. AUTH URL TEST (should return 200 = login page):")
out, err, rc = ssh_exec("""curl -s -k -o /dev/null -w '%{http_code}' 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test12345&state=teste' --max-time 10""")
print(f"   Keycloak auth HTTP: {out}")

# 7. Test oauth.html is accessible
print("\n7. OAUTH.HTML ACCESSIBILITY:")
out, err, rc = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   HTTP: {out}")

# 8. Check containers status
print("\n8. ALL JITSI CONTAINERS:")
out, err, rc = ssh_exec("docker ps --filter 'name=jitsi' --format '{{.Names}} {{.Status}}'")
print(f"   {out}")

# 9. Now check Prosody's token verification module to understand what claims it validates
print("\n9. PROSODY TOKEN VERIFICATION MODULE:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find / -name 'token_verification.lib.lua' 2>/dev/null")
if out.strip():
    mod_path = out.strip().split('\n')[0]
    out2, err2, rc2 = ssh_exec(f"docker exec jitsi-meet-prosody-1 cat {mod_path} 2>/dev/null")
    # Show key parts: verify function, claim checks
    lines = out2.split('\n')
    for i, line in enumerate(lines):
        if any(x in line.lower() for x in ['function verify', 'function validate', 'room', 'context', 'iss', 'aud', 'sub', 'exp', 'not_before', 'claims', 'asap_key_server', 'secret']):
            start = max(0, i-1)
            end = min(len(lines), i+3)
            print(f"   Line {i+1}: {'|'.join(lines[start:end])}")

# 10. Check Prosody's full lua JWT library
print("\n10. PROSODY JWT LIBRARY:")
out, err, rc = ssh_exec("docker exec jitsi-meet-prosody-1 find / -name 'luajwtjitsi*' -o -name 'jwt.lua' 2>/dev/null | head -5")
print(f"   JWT lib paths: {out}")
if out.strip():
    jwt_path = out.strip().split('\n')[0]
    out2, err2, rc2 = ssh_exec(f"docker exec jitsi-meet-prosody-1 cat {jwt_path} 2>/dev/null | grep -n 'function\\|verify\\|decode\\|algorithm\\|key_server\\|asap' | head -20")
    print(f"   JWT lib functions:\n{out2}")

print("\n=== DEPLOY COMPLETE ===")

