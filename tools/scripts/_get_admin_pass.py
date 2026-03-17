import urllib.request, urllib.parse, json

KC = "http://127.0.0.1:8080"

# token admin keycloak
payload = urllib.parse.urlencode({
    "client_id": "admin-cli",
    "username": "admin",
    "password": "admin_dev_password",
    "grant_type": "password"
}).encode()
req = urllib.request.Request(KC + "/realms/master/protocol/openid-connect/token", data=payload, method="POST")
token = json.loads(urllib.request.urlopen(req, timeout=5).read())["access_token"]

# buscar usuario platform-admin
req2 = urllib.request.Request(
    KC + "/admin/realms/intellicare/users?username=platform-admin",
    headers={"Authorization": f"Bearer {token}"}
)
users = json.loads(urllib.request.urlopen(req2, timeout=5).read())
if users:
    u = users[0]
    print(f"ID:       {u['id']}")
    print(f"Username: {u['username']}")
    print(f"Email:    {u['email']}")
    print(f"Enabled:  {u['enabled']}")
    # credenciais nao sao expostas pela API — precisamos resetar ou verificar no seed
    print("\n[INFO] Senha nao exposta pela API do Keycloak.")
    print("Verificando seed_demo.py para a senha padrao...")
else:
    print("Usuario platform-admin nao encontrado")
