import urllib.request
import urllib.parse
import json

BASE = "http://127.0.0.1:9000"
KC   = "http://127.0.0.1:8080"

print("=" * 60)
print("VERIFICACAO DO AMBIENTE ADMIN")
print("=" * 60)

# 1. Health da API
try:
    res = urllib.request.urlopen(BASE + "/health", timeout=5)
    data = json.loads(res.read())
    print(f"\n[API] /health => {res.getcode()} | {data}")
except Exception as e:
    print(f"\n[API] /health => ERRO: {e}")

# 2. Rotas admin (espera 401 sem token)
admin_routes = [
    "/admin/dashboard/stats",
    "/admin/tenants",
    "/admin/audit",
]
print("\n[API] Rotas admin (sem token — espera 401):")
for route in admin_routes:
    try:
        urllib.request.urlopen(BASE + route, timeout=5)
        print(f"  200  {route}  ← INESPERADO (deveria pedir auth)")
    except urllib.error.HTTPError as e:
        print(f"  {e.code}  {route}  {'OK' if e.code == 401 else 'INESPERADO'}")
    except Exception as e:
        print(f"  ERR  {route}  {e}")

# 3. Admin-UI static
try:
    res = urllib.request.urlopen(BASE + "/admin-ui/", timeout=5)
    print(f"\n[STATIC] /admin-ui/ => {res.getcode()} OK")
except Exception as e:
    print(f"\n[STATIC] /admin-ui/ => ERRO: {e}")

# 4. Keycloak realm
try:
    url = KC + "/realms/intellicare"
    res = urllib.request.urlopen(url, timeout=5)
    data = json.loads(res.read())
    print(f"\n[KEYCLOAK] realm 'intellicare' => OK | realm: {data.get('realm')}")
except Exception as e:
    print(f"\n[KEYCLOAK] realm 'intellicare' => ERRO: {e}")

# 5. Listar usuarios via Keycloak Admin API
print("\n[KEYCLOAK] Buscando usuarios com role PLATFORM_ADMIN...")
try:
    # obter token admin
    payload = urllib.parse.urlencode({
        "client_id": "admin-cli",
        "username": "admin",
        "password": "admin_dev_password",
        "grant_type": "password"
    }).encode()
    req = urllib.request.Request(
        KC + "/realms/master/protocol/openid-connect/token",
        data=payload,
        method="POST"
    )
    res = urllib.request.urlopen(req, timeout=5)
    token = json.loads(res.read())["access_token"]

    # buscar usuarios do realm intellicare
    req2 = urllib.request.Request(
        KC + "/admin/realms/intellicare/users?max=50",
        headers={"Authorization": f"Bearer {token}"}
    )
    res2 = urllib.request.urlopen(req2, timeout=5)
    users = json.loads(res2.read())

    print(f"  Total de usuarios no realm: {len(users)}")
    for u in users:
        print(f"  - {u.get('username','?')} | {u.get('email','?')} | enabled={u.get('enabled')}")

    # buscar quem tem role PLATFORM_ADMIN
    req3 = urllib.request.Request(
        KC + "/admin/realms/intellicare/roles/PLATFORM_ADMIN/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        res3 = urllib.request.urlopen(req3, timeout=5)
        admins = json.loads(res3.read())
        print(f"\n  Usuarios com PLATFORM_ADMIN: {len(admins)}")
        for a in admins:
            print(f"  * {a.get('username')} ({a.get('email')})")
    except urllib.error.HTTPError as e:
        print(f"  Role PLATFORM_ADMIN: {e.code} - pode nao existir ainda")

except Exception as e:
    print(f"  ERRO ao acessar Keycloak Admin API: {e}")

print("\n" + "=" * 60)
