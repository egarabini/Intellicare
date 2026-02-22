import paramiko
import json
import base64
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

print("=== END-TO-END AUTH FLOW TEST ===\n")

# 1. Get a real id_token from Keycloak via direct access grant
# This simulates what the browser would get after Keycloak login
print("1. GET KEYCLOAK ID_TOKEN:")
out, err, rc = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=jitsi-meet&grant_type=password&username=admin%40saudeplanner.com.br&password=Admin%40123&scope=openid email profile'""")
try:
    token_resp = json.loads(out)
    if 'error' in token_resp:
        print(f"   Error: {token_resp['error']} - {token_resp.get('error_description', '')}")
        # Try with different user credentials
        print("   Trying with egarabini@gmail.com...")
        out, err, rc = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=jitsi-meet&grant_type=password&username=egarabini%40gmail.com&password=Crazy%2357LB&scope=openid email profile'""")
        token_resp = json.loads(out)
        if 'error' in token_resp:
            print(f"   Error: {token_resp['error']} - {token_resp.get('error_description', '')}")
            
            # List users and try to get token with different approach
            print("   Trying to get admin token and list user passwords...")
            out_admin, _, _ = ssh_exec("""curl -s -k -X POST 'https://keycloak.gsi.srv.br/realms/master/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=egarabini%40gmail.com&password=Crazy%2357LB&grant_type=password&client_id=admin-cli'""")
            admin_resp = json.loads(out_admin)
            admin_token = admin_resp.get('access_token')
            if admin_token:
                out_users, _, _ = ssh_exec(f"""curl -s -k -H 'Authorization: Bearer {admin_token}' 'https://keycloak.gsi.srv.br/admin/realms/bemcuidar/users?briefRepresentation=false' | python3 -m json.tool""")
                # Extract just usernames
                users = json.loads(out_users.replace('\n', ''))
                for u in users:
                    print(f"      User: {u.get('username')} enabled={u.get('enabled')} email={u.get('email')}")
    else:
        print(f"   Got token response with keys: {list(token_resp.keys())}")
        id_token = token_resp.get('id_token', '')
        access_token = token_resp.get('access_token', '')
        
        if id_token:
            print(f"\n   ID_TOKEN length: {len(id_token)}")
            # Decode JWT header and payload (without verification)
            parts = id_token.split('.')
            if len(parts) == 3:
                # Decode header
                header_b64 = parts[0] + '==' # padding
                try:
                    header = json.loads(base64.urlsafe_b64decode(header_b64))
                    print(f"   JWT Header: {json.dumps(header, indent=2)}")
                except:
                    pass
                
                # Decode payload
                payload_b64 = parts[1] + '=='
                try:
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                    print(f"\n   JWT Payload (claims):")
                    print(f"      iss: {payload.get('iss')}")
                    print(f"      aud: {payload.get('aud')}")
                    print(f"      sub: {payload.get('sub')}")
                    print(f"      azp: {payload.get('azp')}")
                    print(f"      exp: {payload.get('exp')}")
                    print(f"      iat: {payload.get('iat')}")
                    print(f"      nonce: {payload.get('nonce')}")
                    print(f"      session_state: {payload.get('session_state')}")
                    print(f"      name: {payload.get('name')}")
                    print(f"      email: {payload.get('email')}")
                    print(f"      preferred_username: {payload.get('preferred_username')}")
                    print(f"      room: {payload.get('room', 'NOT PRESENT')}")
                    print(f"      context: {payload.get('context', 'NOT PRESENT')}")
                    
                    # Check compatibility with Prosody
                    print(f"\n   PROSODY COMPATIBILITY CHECK:")
                    iss_ok = payload.get('iss') == 'https://keycloak.gsi.srv.br/realms/bemcuidar'
                    aud = payload.get('aud')
                    aud_ok = aud == 'jitsi-meet' or (isinstance(aud, list) and 'jitsi-meet' in aud)
                    alg_ok = header.get('alg') == 'RS256'
                    kid_ok = header.get('kid') is not None
                    
                    print(f"      iss matches: {iss_ok} ({payload.get('iss')})")
                    print(f"      aud matches: {aud_ok} ({aud})")
                    print(f"      alg=RS256: {alg_ok} ({header.get('alg')})")
                    print(f"      kid present: {kid_ok} ({header.get('kid')})")
                    print(f"      room claim: {'MISSING (OK - asap_require_room_claim=false)' if not payload.get('room') else payload.get('room')}")
                    
                    # STEP 2: Try using this token to access Jitsi via BOSH
                    print(f"\n2. TEST TOKEN WITH PROSODY (via meet.gsi.srv.br):")
                    print(f"   Token (first 50 chars): {id_token[:50]}...")
                    
                    # Test accessing meet with JWT in URL
                    out2, err2, rc2 = ssh_exec(f"curl -s -k -o /dev/null -w '%{{http_code}}' 'https://meet.gsi.srv.br/teste?jwt={id_token[:200]}...' --max-time 10")
                    print(f"   HTTP response: {out2}")
                    
                except Exception as e:
                    print(f"   Error decoding: {e}")
        
        # 3. Check if Keycloak's kid matches JWKS
        print(f"\n3. VERIFY KID IN JWKS:")
        if id_token:
            parts = id_token.split('.')
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            kid = header.get('kid')
            out_jwks, _, _ = ssh_exec("curl -s -k 'https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/certs'")
            jwks = json.loads(out_jwks)
            found = False
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    found = True
                    print(f"   KID '{kid}' FOUND in JWKS ✓")
                    print(f"   Key type: {key.get('kty')}, alg: {key.get('alg')}, use: {key.get('use')}")
                    break
            if not found:
                print(f"   KID '{kid}' NOT FOUND in JWKS ✗")

except Exception as e:
    print(f"   Error: {e}")
    print(f"   Raw response: {out[:500]}")

# 4. Check Prosody logs after test
print(f"\n4. PROSODY LOGS (recent):")
out, err, rc = ssh_exec("docker logs jitsi-meet-prosody-1 --tail 10 2>&1")
print(f"   {out}")

# 5. Provide test URLs for the user
print(f"\n5. TEST URLs FOR USER:")
print(f"   Direct Keycloak login (paste in browser):")
print(f"   https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth?client_id=jitsi-meet&redirect_uri=https%3A%2F%2Fmeet.gsi.srv.br%2Fstatic%2Foauth.html&response_type=id_token&scope=openid%20email%20profile&nonce=test12345abc&state=teste")
print(f"\n   Or just visit: https://meet.gsi.srv.br/teste")
print(f"   Jitsi should redirect to Keycloak for login")

print("\n=== END ===")
