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

CONFIG_DIR = "/root/.jitsi-meet-cfg"
COMPOSE_DIR = "/root/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

print("=== FIX: REDIRECT DIRETO VIA CUSTOM-CONFIG.JS ===\n")

# 1. Primeiro - checar logs recentes do Prosody
print("1. PROSODY LOGS (ultimas linhas):")
out, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 10 2>&1")
print(out[:2000])

# 2. O problema: o tokenAuthUrlAutoRedirect do Jitsi so funciona APOS um login
#    anterior bem-sucedido. Na primeira visita, o Jitsi mostra "Esperando anfitriao"
#    e o botao "Eu sou o anfitriao" tenta abrir um POPUP que o browser bloqueia.
#
#    Solucao: Injetar JavaScript no custom-config.js que redireciona AUTOMATICAMENTE
#    para o Keycloak se nao houver JWT na URL. Isso bypassa o mecanismo de popup.

print("\n2. Criando custom-config.js com redirect automatico:")
custom_config = r"""// Keycloak OIDC - Redirect automatico para login
// Se o usuario acessa uma sala sem JWT, redireciona para Keycloak
(function() {
    // So redireciona se:
    // 1. Estamos numa pagina de sala (path tem nome da sala)
    // 2. Nao temos JWT na URL
    // 3. Nao estamos no oauth.html callback
    var path = window.location.pathname;
    var search = window.location.search;
    var hasJwt = search.indexOf('jwt=') !== -1;
    var isRoom = path.length > 1 && path !== '/static/oauth.html';
    
    if (isRoom && !hasJwt) {
        var room = path.replace(/^\//, '').replace(/\/$/, '');
        if (room && room !== '' && room.indexOf('.') === -1) {
            var nonce = '';
            var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            for (var i = 0; i < 32; i++) {
                nonce += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            var authUrl = 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth'
                + '?client_id=jitsi-meet'
                + '&redirect_uri=' + encodeURIComponent('https://meet.gsi.srv.br/static/oauth.html')
                + '&response_type=id_token'
                + '&scope=openid%20email%20profile'
                + '&nonce=' + nonce
                + '&state=' + encodeURIComponent(room);
            window.location.replace(authUrl);
        }
    }
})();
"""
# Deploy custom-config.js
cmd = f"""cat > {CONFIG_DIR}/web/custom-config.js << 'CUSTOMEOF'
{custom_config}
CUSTOMEOF"""
ssh_exec(cmd)
out, _, _ = ssh_exec(f"cat {CONFIG_DIR}/web/custom-config.js")
print(f"   Conteudo:\n{out}")

# 3. Restart containers (necessario para regenerar config.js com custom-config.js)
print("\n3. Reiniciando containers:")
out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml down 2>&1", timeout=60)
print(f"   Down OK")
time.sleep(3)
out, _, _ = ssh_exec(f"cd {COMPOSE_DIR} && docker compose -f docker-compose-jitsi.yml up -d 2>&1", timeout=120)
print(f"   Up OK")
time.sleep(12)

# 4. Verificar containers
print("\n4. Status containers:")
out, _, _ = ssh_exec("docker ps --filter name=jitsi-meet --format 'table {{.Names}}\t{{.Status}}' 2>&1")
print(out)

# 5. Verificar se custom-config.js foi incluido no config.js final
print("5. Config.js final (ultimas 30 linhas):")
out, _, _ = ssh_exec("docker exec jitsi-meet-web-1 tail -30 /config/config.js 2>/dev/null")
print(out)

# 6. Testar o redirect (simular browser visitando sala)
print("\n6. Teste de redirect:")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w 'HTTP_%{http_code} Redirect:%{redirect_url}' -L --max-redirs 0 'https://meet.gsi.srv.br/teste' --max-time 10 2>&1")
print(f"   meet.gsi.srv.br/teste: {out}")

# O redirect acontece via JavaScript, nao via HTTP 302
# Entao o curl sempre retorna 200 com o HTML
# Verificar se o JavaScript esta no HTML servido
out, _, _ = ssh_exec("curl -s -k 'https://meet.gsi.srv.br/teste' --max-time 10 | grep -c 'keycloak'")
print(f"   HTML contem referencia keycloak: {out.strip()} vezes")

# 7. Verificar que oauth.html funciona
print("\n7. oauth.html acessivel:")
out, _, _ = ssh_exec("curl -s -k -o /dev/null -w '%{http_code}' 'https://meet.gsi.srv.br/static/oauth.html' --max-time 10")
print(f"   HTTP: {out}")

# 8. Gerar URL de teste para o usuario
print("\n8. URLs para teste manual:")
print(f"   Sala: https://meet.gsi.srv.br/teste")
print(f"   Keycloak direto: https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=manual123test&state=teste")

print("\n=== DONE ===")
