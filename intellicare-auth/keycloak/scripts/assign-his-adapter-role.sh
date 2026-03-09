#!/bin/bash
# =============================================================================
# Atribui a role HIS_ADAPTER ao service account intellicare-bridge-dev
# =============================================================================
# Uso: ./assign-his-adapter-role.sh
#      KEYCLOAK_URL=http://localhost:8080 ./assign-his-adapter-role.sh
#
# Pré-requisitos: Keycloak rodando, realm bemcuidar importado, curl e jq
# =============================================================================

set -e

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-changeme}"
REALM="${KEYCLOAK_REALM:-bemcuidar}"
CLIENT_ID="intellicare-bridge-dev"
ROLE_NAME="HIS_ADAPTER"

echo "=== Atribuindo role $ROLE_NAME ao service account $CLIENT_ID ==="
echo "Keycloak: $KEYCLOAK_URL | Realm: $REALM"

# 1. Obter token admin
echo ""
echo "[1/4] Obtendo token admin..."
TOKEN_RESP=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD")
TOKEN=$(echo "$TOKEN_RESP" | jq -r '.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "ERRO: Falha ao obter token. Verifique Keycloak e credenciais admin."
  exit 1
fi
echo "   Token obtido."

# 2. Obter client UUID
echo ""
echo "[2/4] Buscando client $CLIENT_ID..."
CLIENTS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients?clientId=$CLIENT_ID")
CLIENT_UUID=$(echo "$CLIENTS" | jq -r '.[0].id')
if [ "$CLIENT_UUID" = "null" ] || [ -z "$CLIENT_UUID" ]; then
  echo "ERRO: Client '$CLIENT_ID' nao encontrado. Importe o realm bemcuidar primeiro."
  exit 1
fi
echo "   Client UUID: $CLIENT_UUID"

# 3. Obter service account user
echo ""
echo "[3/4] Obtendo service account user..."
SA_USER=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID/service-account-user")
USER_ID=$(echo "$SA_USER" | jq -r '.id')
if [ "$USER_ID" = "null" ] || [ -z "$USER_ID" ]; then
  echo "ERRO: Service account nao encontrado. Verifique se o client tem serviceAccountsEnabled=true."
  exit 1
fi
echo "   User ID: $USER_ID"

# 4. Obter role e atribuir
echo ""
echo "[4/4] Atribuindo role $ROLE_NAME..."
ROLE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$KEYCLOAK_URL/admin/realms/$REALM/roles/$ROLE_NAME")
ROLE_ID=$(echo "$ROLE" | jq -r '.id')
if [ "$ROLE_ID" = "null" ] || [ -z "$ROLE_ID" ]; then
  echo "ERRO: Role '$ROLE_NAME' nao encontrada no realm."
  exit 1
fi
ROLE_PAYLOAD="[{\"id\":\"$ROLE_ID\",\"name\":\"$ROLE_NAME\"}]"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$ROLE_PAYLOAD" \
  "$KEYCLOAK_URL/admin/realms/$REALM/users/$USER_ID/role-mappings/realm")
if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "   Role atribuida com sucesso."
else
  # Verificar se já tem a role
  CURRENT=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$KEYCLOAK_URL/admin/realms/$REALM/users/$USER_ID/role-mappings/realm")
  if echo "$CURRENT" | jq -e ".[] | select(.name==\"$ROLE_NAME\")" >/dev/null 2>&1; then
    echo "   Role ja estava atribuida."
  else
    echo "ERRO: HTTP $HTTP_CODE ao atribuir role."
    exit 1
  fi
fi

echo ""
echo "=== Concluido ==="
echo "O service account $CLIENT_ID agora tem a role $ROLE_NAME."
echo ""
echo "Teste o token:"
echo "  curl -s -X POST $KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token \\"
echo "    -d 'grant_type=client_credentials' \\"
echo "    -d 'client_id=$CLIENT_ID' \\"
echo "    -d 'client_secret=bridge-dev-secret-change-in-production' | jq .access_token"
