#!/usr/bin/env bash
# ============================================================================
# IntelliCare — DNS + Certificate Verification Script
# ============================================================================
# Run: bash scripts/dns/verify_certs.sh
# ============================================================================
set -euo pipefail

# ── Configuration ───────────────────────────────────────────
DOMAIN_PLATFORM="${DOMAIN_PLATFORM:-intellicare.ia.br}"
DOMAIN_MODULES="${DOMAIN_MODULES:-saudeplanner.com.br}"
SERVER_IP="${SERVER_IP:-}"

PASS=0
FAIL=0
WARN=0

check_pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
check_fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
check_warn() { echo "  ⚠️  $1"; WARN=$((WARN + 1)); }

echo "============================================================"
echo "  IntelliCare — DNS + Certificate Verification"
echo "  $(date)"
echo "============================================================"
echo ""

# ════════════════════════════════════════════════════════════
# 1. DNS Resolution Check
# ════════════════════════════════════════════════════════════
echo "📡 1/3 — DNS Resolution"
echo ""

SUBDOMAINS_PLATFORM=(
    "admin.${DOMAIN_PLATFORM}"
    "portal.${DOMAIN_PLATFORM}"
    "api.${DOMAIN_PLATFORM}"
    "keycloak.${DOMAIN_PLATFORM}"
    "traefik.${DOMAIN_PLATFORM}"
)

SUBDOMAINS_MODULES=(
    "oswaldo.${DOMAIN_MODULES}"
    "florence.${DOMAIN_MODULES}"
    "zilda.${DOMAIN_MODULES}"
)

echo "  Domínio: ${DOMAIN_PLATFORM}"
for SUB in "${SUBDOMAINS_PLATFORM[@]}"; do
    RESOLVED_IP=$(dig +short "$SUB" A 2>/dev/null | head -1)
    if [ -n "$RESOLVED_IP" ]; then
        if [ -n "$SERVER_IP" ] && [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
            check_warn "$SUB → $RESOLVED_IP (esperado: $SERVER_IP)"
        else
            check_pass "$SUB → $RESOLVED_IP"
        fi
    else
        check_fail "$SUB → SEM RESOLUÇÃO"
    fi
done

echo ""
echo "  Domínio: ${DOMAIN_MODULES}"
for SUB in "${SUBDOMAINS_MODULES[@]}"; do
    RESOLVED_IP=$(dig +short "$SUB" A 2>/dev/null | head -1)
    if [ -n "$RESOLVED_IP" ]; then
        check_pass "$SUB → $RESOLVED_IP"
    else
        check_fail "$SUB → SEM RESOLUÇÃO"
    fi
done

# ════════════════════════════════════════════════════════════
# 2. HTTPS Certificate Check
# ════════════════════════════════════════════════════════════
echo ""
echo "🔒 2/3 — SSL Certificates"
echo ""

check_cert() {
    local DOMAIN="$1"
    local CERT_INFO

    CERT_INFO=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null \
        | openssl x509 -noout -dates -subject 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$CERT_INFO" ]; then
        EXPIRY=$(echo "$CERT_INFO" | grep "notAfter" | cut -d= -f2)
        SUBJECT=$(echo "$CERT_INFO" | grep "subject" | cut -d= -f2-)
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

        if [ "$DAYS_LEFT" -gt 30 ]; then
            check_pass "$DOMAIN — válido por $DAYS_LEFT dias"
        elif [ "$DAYS_LEFT" -gt 0 ]; then
            check_warn "$DOMAIN — expira em $DAYS_LEFT dias!"
        else
            check_fail "$DOMAIN — EXPIRADO!"
        fi
    else
        check_warn "$DOMAIN — sem certificado SSL (Traefik pode estar pendente)"
    fi
}

for SUB in "${SUBDOMAINS_PLATFORM[@]}"; do
    check_cert "$SUB"
done

for SUB in "${SUBDOMAINS_MODULES[@]}"; do
    check_cert "$SUB"
done

# ════════════════════════════════════════════════════════════
# 3. HTTP Endpoint Check (via HTTPS)
# ════════════════════════════════════════════════════════════
echo ""
echo "🌐 3/3 — HTTPS Endpoint Connectivity"
echo ""

ENDPOINTS=(
    "https://admin.${DOMAIN_PLATFORM}/api/v1/health"
    "https://portal.${DOMAIN_PLATFORM}/"
    "https://api.${DOMAIN_PLATFORM}/v1/oswaldo/api/v1/health"
    "https://api.${DOMAIN_PLATFORM}/v1/florence/api/v1/health"
)

for URL in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$URL" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" == "200" ]; then
        check_pass "$URL → HTTP $HTTP_CODE"
    elif [ "$HTTP_CODE" == "000" ]; then
        check_fail "$URL → TIMEOUT/UNREACHABLE"
    elif [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
        check_pass "$URL → HTTP $HTTP_CODE (redirect)"
    else
        check_warn "$URL → HTTP $HTTP_CODE"
    fi
done

# ════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "  Resultado: ${PASS} OK, ${WARN} avisos, ${FAIL} falhas"

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
    echo "  ✅ Tudo configurado corretamente!"
elif [ "$FAIL" -eq 0 ]; then
    echo "  ⚠️  Configuração OK mas com avisos"
else
    echo "  ❌ Há problemas que precisam de correção"
fi
echo "============================================================"

exit "$FAIL"
