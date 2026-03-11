#!/bin/bash
set -euo pipefail

# Uso: KC_PASS=senha bash scripts/patch_keycloak_client.sh
KC_URL="${KC_URL:-http://localhost:8080}"
KC_REALM="${KC_REALM:-bemcuidar}"
KC_ADMIN="${KC_ADMIN:-admin}"
KC_PASS="${KC_PASS:-Soeuso410863}"

TOKEN=$(curl -s -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli&username=$KC_ADMIN&password=$KC_PASS&grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

CLIENT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KC_URL/admin/realms/$KC_REALM/clients?clientId=intellicare-portal" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

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
print(json.dumps(d))
")

curl -s -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$KC_URL/admin/realms/$KC_REALM/clients/$CLIENT_ID" \
  -d "$UPDATED_JSON"

echo "Done. Client intellicare-portal atualizado sem perda de configuracao."
