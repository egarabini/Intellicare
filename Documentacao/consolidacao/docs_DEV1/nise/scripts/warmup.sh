#!/bin/bash
################################################################################
# NISE MVP - WARM-UP SCRIPT
################################################################################
# Projeto: NISE - Treinamento Assistido
# Objetivo: Warm-up do sistema antes da validação
# Data: 27/03/2026
# Responsável: DEV1
################################################################################

echo "🚀 NISE MVP - WARM-UP SCRIPT"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

################################################################################
# 1. VERIFICAR SERVIÇOS
################################################################################

echo "📋 1. Verificando serviços Docker..."
echo ""

if ! docker ps | grep -q "nise"; then
    echo -e "${RED}❌ Nenhum container NISE encontrado!${NC}"
    echo "Execute: docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Containers Docker rodando${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep nise
echo ""

################################################################################
# 2. HEALTH CHECKS
################################################################################

echo "🏥 2. Executando Health Checks..."
echo ""

# Backend Health
echo -n "   Backend: "
if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FALHOU${NC}"
    exit 1
fi

# Florence Health
echo -n "   Florence: "
if curl -s -f "${BASE_URL}/api/v1/florence/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Florence pode não estar disponível${NC}"
fi

# Ollama Health
echo -n "   Ollama: "
if curl -s -f "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Ollama pode não estar disponível${NC}"
fi

echo ""

################################################################################
# 3. WARM-UP DE ENDPOINTS
################################################################################

echo "🔥 3. Aquecendo endpoints (warm-up)..."
echo ""

# Patient endpoints
echo -n "   GET /api/v1/patients: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/api/v1/patients")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

# Observation endpoints
echo -n "   GET /api/v1/observations: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/api/v1/observations")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

# Practitioner endpoints
echo -n "   GET /api/v1/practitioners: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/api/v1/practitioners")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

# Encounter endpoints
echo -n "   GET /api/v1/encounters: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/api/v1/encounters")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

echo ""

################################################################################
# 4. WARM-UP FLORENCE
################################################################################

echo "🤖 4. Aquecendo Florence AI..."
echo ""

FLORENCE_REQUEST='{
  "message": "teste de warm-up",
  "session_id": "warmup-session"
}'

echo -n "   POST /api/v1/florence/chat: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -X POST "${BASE_URL}/api/v1/florence/chat" \
  -H "Content-Type: application/json" \
  -d "$FLORENCE_REQUEST")

if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${YELLOW}⚠️  $RESPONSE (Florence pode estar em modo fallback)${NC}"
fi

echo ""

################################################################################
# 5. VERIFICAR SWAGGER
################################################################################

echo "📚 5. Verificando Swagger UI..."
echo ""

echo -n "   GET /docs: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/docs")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

echo -n "   GET /openapi.json: "
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/api/v1/openapi.json")
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ $RESPONSE${NC}"
fi

echo ""

################################################################################
# 6. RESUMO
################################################################################

echo "================================"
echo -e "${GREEN}✅ WARM-UP CONCLUÍDO!${NC}"
echo ""
echo "Sistema pronto para validação:"
echo "  - Swagger UI: ${BASE_URL}/docs"
echo "  - ReDoc: ${BASE_URL}/redoc"
echo "  - Health: ${BASE_URL}/health"
echo ""
echo "Próximo passo: Executar validação completa"
echo "  ./scripts/validate.sh"
echo ""

