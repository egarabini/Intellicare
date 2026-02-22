#!/bin/bash
################################################################################
# NISE MVP - VALIDATION SCRIPT
################################################################################
# Projeto: NISE - Treinamento Assistido
# Objetivo: Validação completa do sistema antes da apresentação
# Data: 27/03/2026
# Responsável: DEV1
################################################################################

echo "🎯 NISE MVP - VALIDATION SCRIPT"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

################################################################################
# HELPER FUNCTIONS
################################################################################

test_endpoint() {
    local METHOD=$1
    local ENDPOINT=$2
    local EXPECTED_CODE=$3
    local DATA=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "   [$TOTAL_TESTS] $METHOD $ENDPOINT: "
    
    if [ -z "$DATA" ]; then
        RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X "$METHOD" "${BASE_URL}${ENDPOINT}")
    else
        RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
            -X "$METHOD" "${BASE_URL}${ENDPOINT}" \
            -H "Content-Type: application/json" \
            -d "$DATA")
    fi
    
    if [ "$RESPONSE" -eq "$EXPECTED_CODE" ]; then
        echo -e "${GREEN}✅ $RESPONSE${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ $RESPONSE (esperado: $EXPECTED_CODE)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

################################################################################
# 1. HEALTH CHECKS
################################################################################

echo "🏥 1. Health Checks"
echo ""

test_endpoint "GET" "/health" 200
test_endpoint "GET" "/api/v1/florence/health" 200

echo ""

################################################################################
# 2. PATIENT ENDPOINTS
################################################################################

echo "👤 2. Patient Endpoints"
echo ""

# Create Patient
PATIENT_DATA='{
  "resourceType": "Patient",
  "identifier": [
    {
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
      "value": "12345678901"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Silva",
      "given": ["João", "Carlos"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-15"
}'

echo -n "   Creating test patient... "
PATIENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/patients" \
    -H "Content-Type: application/json" \
    -d "$PATIENT_DATA")
PATIENT_ID=$(echo "$PATIENT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$PATIENT_ID" ]; then
    echo -e "${GREEN}✅ Created (ID: $PATIENT_ID)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Failed to create${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test Patient endpoints
test_endpoint "GET" "/api/v1/patients" 200
if [ -n "$PATIENT_ID" ]; then
    test_endpoint "GET" "/api/v1/patients/$PATIENT_ID" 200
fi

echo ""

################################################################################
# 3. PRACTITIONER ENDPOINTS
################################################################################

echo "👨‍⚕️ 3. Practitioner Endpoints"
echo ""

PRACTITIONER_DATA='{
  "resourceType": "Practitioner",
  "identifier": [
    {
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
      "value": "CRM-SP-123456"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Santos",
      "given": ["Maria", "Fernanda"],
      "prefix": ["Dra."]
    }
  ]
}'

echo -n "   Creating test practitioner... "
PRACTITIONER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/practitioners" \
    -H "Content-Type: application/json" \
    -d "$PRACTITIONER_DATA")
PRACTITIONER_ID=$(echo "$PRACTITIONER_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$PRACTITIONER_ID" ]; then
    echo -e "${GREEN}✅ Created (ID: $PRACTITIONER_ID)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Failed to create${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

test_endpoint "GET" "/api/v1/practitioners" 200

echo ""

################################################################################
# 4. OBSERVATION ENDPOINTS
################################################################################

echo "🔬 4. Observation Endpoints"
echo ""

test_endpoint "GET" "/api/v1/observations" 200

if [ -n "$PATIENT_ID" ]; then
    OBSERVATION_DATA='{
      "resourceType": "Observation",
      "status": "final",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "2339-0",
            "display": "Glucose [Mass/volume] in Blood"
          }
        ]
      },
      "subject": {
        "reference": "Patient/'$PATIENT_ID'"
      },
      "valueQuantity": {
        "value": 95,
        "unit": "mg/dL",
        "system": "http://unitsofmeasure.org",
        "code": "mg/dL"
      }
    }'
    
    test_endpoint "POST" "/api/v1/observations" 201 "$OBSERVATION_DATA"
fi

echo ""

################################################################################
# 5. ENCOUNTER ENDPOINTS
################################################################################

echo "🏥 5. Encounter Endpoints"
echo ""

test_endpoint "GET" "/api/v1/encounters" 200

echo ""

################################################################################
# 6. FLORENCE AI
################################################################################

echo "🤖 6. Florence AI Assistant"
echo ""

FLORENCE_Q1='{
  "message": "Quais são os campos obrigatórios de um Patient FHIR R4?",
  "session_id": "validation-session"
}'

FLORENCE_Q2='{
  "message": "O que significa o código LOINC 2339-0?",
  "session_id": "validation-session"
}'

test_endpoint "POST" "/api/v1/florence/chat" 200 "$FLORENCE_Q1"
test_endpoint "POST" "/api/v1/florence/chat" 200 "$FLORENCE_Q2"

echo ""

################################################################################
# 7. SWAGGER/OPENAPI
################################################################################

echo "📚 7. Documentation Endpoints"
echo ""

test_endpoint "GET" "/docs" 200
test_endpoint "GET" "/redoc" 200
test_endpoint "GET" "/api/v1/openapi.json" 200

echo ""

################################################################################
# 8. SUMMARY
################################################################################

echo "================================"
echo "📊 VALIDATION SUMMARY"
echo "================================"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Sistema 100% validado e pronto para apresentação!"
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Verifique os erros acima antes da apresentação."
    exit 1
fi

