#!/bin/bash
echo "=== IntelliCare Smoke Test ==="

MODULES=(
    "florence:8001"
    "oswaldo:8002"
    "donabedian:8003"
    "wanda:8004"
    "comunicacao:8005"
    "geralda:8006"
)

PASS=0
FAIL=0

for entry in "${MODULES[@]}"; do
    MODULE="${entry%%:*}"
    PORT="${entry##*:}"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/v1/health" --connect-timeout 5)

    if [ "$HTTP_CODE" == "200" ]; then
        echo "✅ ${MODULE} (porta ${PORT}) — HTTP ${HTTP_CODE}"
        PASS=$((PASS + 1))
    else
        echo "❌ ${MODULE} (porta ${PORT}) — HTTP ${HTTP_CODE}"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "Resultado: ${PASS} OK, ${FAIL} FALHAS de ${#MODULES[@]} módulos"
