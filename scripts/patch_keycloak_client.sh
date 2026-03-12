#!/bin/bash
set -euo pipefail

# Uso: KC_PASS=senha bash scripts/patch_keycloak_client.sh
KC_URL="${KC_URL:-http://localhost:8080}"
KC_REALM="${KC_REALM:-intellicare}"
KC_ADMIN="${KC_ADMIN:-admin}"
KC_PASS="${KC_PASS:-Soeuso410863}"
KC_CLIENT_ID="${KC_CLIENT_ID:-intellicare-portal}"

TOKEN=$(curl -s -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli&username=$KC_ADMIN&password=$KC_PASS&grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

CLIENTS_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KC_URL/admin/realms/$KC_REALM/clients?clientId=$KC_CLIENT_ID")

CLIENT_ID=$(echo "$CLIENTS_JSON" | python3 -c "
import sys, json
clients = json.load(sys.stdin)
if not clients:
    raise SystemExit(2)
print(clients[0]['id'])
") || {
  echo "Erro: client '$KC_CLIENT_ID' nao encontrado no realm '$KC_REALM' em $KC_URL" >&2
  exit 1
}

# GET representacao completa do cliente
CLIENT_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KC_URL/admin/realms/$KC_REALM/clients/$CLIENT_ID")

# Modifica apenas redirectUris e webOrigins, preservando o restante
UPDATED_JSON=$(echo "$CLIENT_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
d['redirectUris'] = [
  'http://localhost:3000/*',
  'http://localhost:5173/*',
  'https://portal.intellicare.ia.br/*',
  'https://admin.intellicare.ia.br/*'
]
d['webOrigins'] = [
  'http://localhost:3000',
  'http://localhost:5173',
  'https://portal.intellicare.ia.br',
  'https://admin.intellicare.ia.br'
]
scopes = list(d.get('defaultClientScopes') or [])
for s in ('openid', 'profile', 'email'):
    if s not in scopes:
        scopes.append(s)
d['defaultClientScopes'] = scopes
print(json.dumps(d))
")

curl -s -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$KC_URL/admin/realms/$KC_REALM/clients/$CLIENT_ID" \
  -d "$UPDATED_JSON"

echo "Done. Client $KC_CLIENT_ID atualizado sem perda de configuracao."
