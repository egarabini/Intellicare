import paramiko
import json
import base64

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

print("=== SET PASSWORD + GET TOKEN ===\n")

# 1. Get admin token
out, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=egarabini%40gmail.com&password=Crazy%2357LB&grant_type=password&client_id=admin-cli'""")
admin_token = json.loads(out)['access_token']
print(f"1. Admin token obtained: {admin_token[:30]}...")

# 2. List users in bemcuidar realm
out, _, _ = ssh_exec(f"curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/users'")
users = json.loads(out)
print(f"\n2. Users in bemcuidar realm:")
for u in users:
    print(f"   {u['id']}: {u.get('username')} email={u.get('email')} enabled={u.get('enabled')}")

# 3. Set password for admin@saudeplanner.com.br
test_user = None
for u in users:
    if u.get('username') == 'admin@saudeplanner.com.br' or u.get('email') == 'admin@saudeplanner.com.br':
        test_user = u
        break
if not test_user and users:
    test_user = users[0]

if test_user:
    user_id = test_user['id']
    username = test_user.get('username')
    print(f"\n3. Setting password for: {username} (id={user_id})")
    out, err, rc = ssh_exec(f"""curl -s -k -X PUT 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/users/{user_id}/reset-password' \
  -H 'Authorization: Bearer {admin_token}' \
  -H 'Content-Type: application/json' \
  -d '{{"type":"password","value":"Test@1234","temporary":false}}'""")
    print(f"   Response: [{out}] RC={rc} Err=[{err[:200]}]")
    
    # 4. Get token with new password
    print(f"\n4. Getting id_token with new password:")
    out, _, _ = ssh_exec(f"""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=jitsi-meet&grant_type=password&username={username}&password=Test%401234&scope=openid%20email%20profile'""")
    
    try:
        token_resp = json.loads(out)
        if 'error' in token_resp:
            print(f"   Error: {token_resp}")
        else:
            id_token = token_resp.get('id_token', '')
            print(f"   Got id_token! Length: {len(id_token)}")
            
            # Decode JWT
            parts = id_token.split('.')
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            print(f"\n   JWT HEADER:")
            print(f"      alg: {header.get('alg')}")
            print(f"      kid: {header.get('kid')}")
            print(f"      typ: {header.get('typ')}")
            
            print(f"\n   JWT CLAIMS:")
            print(f"      iss: {payload.get('iss')}")
            print(f"      aud: {payload.get('aud')}")
            print(f"      sub: {payload.get('sub')}")
            print(f"      azp: {payload.get('azp')}")
            print(f"      name: {payload.get('name')}")
            print(f"      email: {payload.get('email')}")
            print(f"      preferred_username: {payload.get('preferred_username')}")
            print(f"      room: {payload.get('room', 'NOT PRESENT')}")
            print(f"      context: {payload.get('context', 'NOT PRESENT')}")
            
            print(f"\n   PROSODY COMPATIBILITY:")
            iss_ok = payload.get('iss') == 'https://keycloak.gsi.srv.br/realms/bemcuidar'
            aud = payload.get('aud')
            aud_ok = aud == 'jitsi-meet' or (isinstance(aud, list) and 'jitsi-meet' in aud)
            alg_ok = header.get('alg') == 'RS256'
            kid_ok = header.get('kid') is not None
            
            print(f"      ✓ iss matches: {iss_ok}")
            print(f"      ✓ aud matches: {aud_ok} (aud={aud})")
            print(f"      ✓ alg=RS256: {alg_ok}")
            print(f"      ✓ kid present: {kid_ok}")
            print(f"      ✓ room claim: NOT REQUIRED (asap_require_room_claim=false)")
            
            # 5. Verify kid exists in JWKS
            out_jwks, _, _ = ssh_exec("curl -s -k 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/certs'")
            jwks = json.loads(out_jwks)
            kid = header.get('kid')
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    print(f"      ✓ kid in JWKS: FOUND ({kid[:20]}...)")
                    break
            
            # 6. Test the token with Prosody (pass via URL)
            print(f"\n5. TEST: Use token to access meet.gsi.srv.br/teste:")
            # The JWT is passed via URL parameter
            out2, _, _ = ssh_exec(f"curl -s -k -o /dev/null -w '%{{http_code}}' 'https://meet.gsi.srv.br/teste?jwt={id_token}' --max-time 10")
            print(f"   HTTP: {out2}")
            
            # 7. Check Prosody logs after JWT test
            import time
            time.sleep(2)
            print(f"\n6. PROSODY LOGS:")
            out3, _, _ = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 15 2>&1 | grep -E '(error|warn|token|jwt|key|verified|not-allowed)' -i")
            print(f"   {out3 if out3.strip() else '   No relevant log entries'}")
            
            # 8. Store the token for the user to test
            print(f"\n7. FULL TEST URL (paste in browser):")
            print(f"   https://meet.gsi.srv.br/teste?jwt={id_token}")
            
    except Exception as e:
        print(f"   Error: {e}")
        print(f"   Raw: {out[:500]}")

print("\n=== END ===")
