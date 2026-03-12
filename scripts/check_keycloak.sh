#!/bin/bash
# Health check script for local Keycloak setup.

set -euo pipefail

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-intellicare}"

echo "Verificando saude do Keycloak em ${KEYCLOAK_URL}..."

if ! curl -sf "${KEYCLOAK_URL}/health/ready" > /dev/null; then
    echo "ERRO: Keycloak nao esta pronto (${KEYCLOAK_URL}/health/ready)"
    exit 1
fi

if ! curl -sf "${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}" > /dev/null; then
    echo "ERRO: Realm ${KEYCLOAK_REALM} nao encontrado"
    exit 1
fi

WELL_KNOWN="${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/.well-known/openid-configuration"
if ! curl -sf "${WELL_KNOWN}" > /dev/null; then
    echo "ERRO: OpenID configuration indisponivel para realm ${KEYCLOAK_REALM}"
    exit 1
fi

echo "OK: Keycloak saudavel e realm ${KEYCLOAK_REALM} acessivel"
