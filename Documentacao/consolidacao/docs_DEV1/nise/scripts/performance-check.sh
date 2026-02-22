#!/bin/bash
################################################################################
# NISE MVP - PERFORMANCE CHECK SCRIPT
################################################################################
# Projeto: NISE - Treinamento Assistido
# Objetivo: Verificar performance do sistema
# Data: 27/03/2026
# Responsável: DEV1
################################################################################

echo "⚡ NISE MVP - PERFORMANCE CHECK"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Performance targets
API_TARGET_MS=100
FLORENCE_TARGET_MS=3000

################################################################################
# HELPER FUNCTIONS
################################################################################

measure_endpoint() {
    local METHOD=$1
    local ENDPOINT=$2
    local NAME=$3
    local DATA=$4
    
    echo -n "   $NAME: "
    
    # Fazer 5 requisições e pegar a média
    TOTAL_TIME=0
    for i in {1..5}; do
        if [ -z "$DATA" ]; then
            TIME=$(curl -s -w "%{time_total}" -o /dev/null -X "$METHOD" "${BASE_URL}${ENDPOINT}")
        else
            TIME=$(curl -s -w "%{time_total}" -o /dev/null \
                -X "$METHOD" "${BASE_URL}${ENDPOINT}" \
                -H "Content-Type: application/json" \
                -d "$DATA")
        fi
        TOTAL_TIME=$(echo "$TOTAL_TIME + $TIME" | bc)
    done
    
    AVG_TIME=$(echo "scale=3; $TOTAL_TIME / 5" | bc)
    AVG_MS=$(echo "$AVG_TIME * 1000" | bc | cut -d'.' -f1)
    
    if [ "$AVG_MS" -lt "$API_TARGET_MS" ]; then
        echo -e "${GREEN}✅ ${AVG_MS}ms (target: <${API_TARGET_MS}ms)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  ${AVG_MS}ms (target: <${API_TARGET_MS}ms)${NC}"
        return 1
    fi
}

################################################################################
# 1. API ENDPOINTS PERFORMANCE
################################################################################

echo "🚀 1. API Endpoints Performance (avg of 5 requests)"
echo ""

measure_endpoint "GET" "/health" "Health Check"
measure_endpoint "GET" "/api/v1/patients" "GET Patients"
measure_endpoint "GET" "/api/v1/observations" "GET Observations"
measure_endpoint "GET" "/api/v1/practitioners" "GET Practitioners"
measure_endpoint "GET" "/api/v1/encounters" "GET Encounters"

echo ""

################################################################################
# 2. FLORENCE PERFORMANCE
################################################################################

echo "🤖 2. Florence AI Performance"
echo ""

FLORENCE_DATA='{
  "message": "O que é FHIR R4?",
  "session_id": "perf-test"
}'

echo -n "   Florence Chat: "

# Fazer 3 requisições (Florence é mais lento)
TOTAL_TIME=0
for i in {1..3}; do
    TIME=$(curl -s -w "%{time_total}" -o /dev/null \
        -X POST "${BASE_URL}/api/v1/florence/chat" \
        -H "Content-Type: application/json" \
        -d "$FLORENCE_DATA")
    TOTAL_TIME=$(echo "$TOTAL_TIME + $TIME" | bc)
done

AVG_TIME=$(echo "scale=3; $TOTAL_TIME / 3" | bc)
AVG_MS=$(echo "$AVG_TIME * 1000" | bc | cut -d'.' -f1)

if [ "$AVG_MS" -lt "$FLORENCE_TARGET_MS" ]; then
    echo -e "${GREEN}✅ ${AVG_MS}ms (target: <${FLORENCE_TARGET_MS}ms)${NC}"
else
    echo -e "${YELLOW}⚠️  ${AVG_MS}ms (target: <${FLORENCE_TARGET_MS}ms)${NC}"
fi

echo ""

################################################################################
# 3. SWAGGER UI PERFORMANCE
################################################################################

echo "📚 3. Documentation Performance"
echo ""

measure_endpoint "GET" "/docs" "Swagger UI"
measure_endpoint "GET" "/api/v1/openapi.json" "OpenAPI JSON"

echo ""

################################################################################
# 4. SUMMARY
################################################################################

echo "================================"
echo "📊 PERFORMANCE SUMMARY"
echo "================================"
echo ""
echo "Targets:"
echo "  - API Endpoints: <${API_TARGET_MS}ms"
echo "  - Florence Chat: <${FLORENCE_TARGET_MS}ms"
echo ""
echo -e "${GREEN}✅ Performance check completed!${NC}"
echo ""
echo "Nota: Valores podem variar dependendo da carga do sistema."
echo "Execute múltiplas vezes para obter média mais precisa."
echo ""

