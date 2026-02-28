#!/bin/bash
# Deploy e validação em staging para W8-D Production Hardening

set -e

echo "=========================================="
echo "🚀 DEPLOY STAGING - W8-D Production Hardening"
echo "=========================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0;33m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
print_step() { echo -e "${BLUE}▶️  $1${NC}"; }

# Variáveis
STAGING_ENV="${STAGING_ENV:-staging}"
DOCKER_COMPOSE_FILE="docker-compose.full.yml"
MODULES=(
    "intellicare-grahame:8012"
    "intellicare-oswaldo:8002"
    "intellicare-florence:8001"
    "intellicare-wanda:8004"
    "intellicare-donabedian:8003"
    "intellicare-zilda:8007"
    "intellicare-geralda:8006"
    "intellicare-comunicacao:8005"
)

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# 1. Verificar pré-requisitos
echo ""
print_step "1️⃣  Verificando pré-requisitos..."

if ! command -v docker &> /dev/null; then
    print_error "Docker não encontrado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não encontrado"
    exit 1
fi

print_success "Pré-requisitos OK"

# 2. Parar containers antigos
echo ""
print_step "2️⃣  Parando containers antigos..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down || true
print_success "Containers antigos parados"

# 3. Limpar volumes (opcional - comentado por segurança)
# echo ""
# print_step "3️⃣  Limpando volumes..."
# docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
# print_success "Volumes limpos"

# 4. Build das imagens hardened
echo ""
print_step "4️⃣  Building imagens hardened..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
print_success "Build concluído"

# 5. Subir serviços
echo ""
print_step "5️⃣  Subindo serviços em staging..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
print_success "Serviços iniciados"

# 6. Aguardar inicialização
echo ""
print_step "6️⃣  Aguardando inicialização dos serviços..."
sleep 30
print_info "Aguardando 30s para warm-up..."

# 7. Verificar health de cada módulo
echo ""
print_step "7️⃣  Verificando health checks..."

for module_port in "${MODULES[@]}"; do
    IFS=':' read -r module port <<< "$module_port"
    
    echo ""
    echo "Testando: $module (porta $port)"
    
    # Tentar 5 vezes com backoff
    for attempt in {1..5}; do
        if curl -f -s "http://localhost:$port/api/v1/health" > /dev/null 2>&1; then
            print_success "$module está saudável"
            ((TESTS_PASSED++))
            break
        else
            if [ $attempt -eq 5 ]; then
                print_error "$module falhou no health check"
                ((TESTS_FAILED++))
                
                # Mostrar logs do container
                print_info "Últimas 20 linhas de log:"
                docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=20 "$module" || true
            else
                print_info "Tentativa $attempt/5 falhou. Aguardando 5s..."
                sleep 5
            fi
        fi
    done
done

# 8. Testar endpoints críticos
echo ""
print_step "8️⃣  Testando endpoints críticos..."

# Grahame - FHIR metadata
echo ""
echo "Testando: Grahame FHIR metadata"
if curl -f -s "http://localhost:8012/api/v1/fhir/metadata" > /dev/null 2>&1; then
    print_success "FHIR metadata OK"
    ((TESTS_PASSED++))
else
    print_error "FHIR metadata falhou"
    ((TESTS_FAILED++))
fi

# Grahame - HL7v2 health
echo ""
echo "Testando: Grahame HL7v2 health"
if curl -f -s "http://localhost:8012/api/v1/hl7v2/health" > /dev/null 2>&1; then
    print_success "HL7v2 health OK"
    ((TESTS_PASSED++))
else
    print_error "HL7v2 health falhou"
    ((TESTS_FAILED++))
fi

# Wanda - info
echo ""
echo "Testando: Wanda info"
if curl -f -s "http://localhost:8004/api/v1/info" > /dev/null 2>&1; then
    print_success "Wanda info OK"
    ((TESTS_PASSED++))
else
    print_error "Wanda info falhou"
    ((TESTS_FAILED++))
fi

# 9. Verificar imagens hardened
echo ""
print_step "9️⃣  Verificando características hardened..."

for module_port in "${MODULES[@]}"; do
    IFS=':' read -r module port <<< "$module_port"
    
    echo ""
    echo "Verificando: $module"
    
    # Verificar se está rodando como non-root
    CONTAINER_ID=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q "$module")
    
    if [ -n "$CONTAINER_ID" ]; then
        USER=$(docker exec "$CONTAINER_ID" whoami 2>/dev/null || echo "unknown")
        
        if [ "$USER" = "nobody" ] || [ "$USER" = "65534" ]; then
            print_success "$module rodando como non-root ($USER)"
            ((TESTS_PASSED++))
        else
            print_error "$module rodando como root ou usuário desconhecido ($USER)"
            ((TESTS_FAILED++))
        fi
    else
        print_error "$module container não encontrado"
        ((TESTS_FAILED++))
    fi
done

# 10. Testar Redis failover (se script existir)
echo ""
print_step "🔟 Testando Redis failover..."

if [ -f "scripts/test_redis_failover.py" ]; then
    if python3 scripts/test_redis_failover.py --api-url "http://localhost:8012"; then
        print_success "Redis failover test passou"
        ((TESTS_PASSED++))
    else
        print_error "Redis failover test falhou"
        ((TESTS_FAILED++))
    fi
else
    print_info "Script de teste Redis failover não encontrado. Pulando."
fi

# 11. Relatório final
echo ""
echo "=========================================="
echo "📊 RELATÓRIO DE VALIDAÇÃO STAGING"
echo "=========================================="
echo ""
echo "✅ Testes passados: $TESTS_PASSED"
echo "❌ Testes falhados: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "DEPLOY STAGING VALIDADO COM SUCESSO!"
    echo ""
    echo "🎉 Todos os testes passaram!"
    echo ""
    echo "Próximos passos:"
    echo "1. Monitorar logs por 24h"
    echo "2. Executar testes de carga"
    echo "3. Validar com stakeholders"
    echo "4. Preparar deploy em produção"
    exit 0
else
    print_error "DEPLOY STAGING FALHOU EM ALGUNS TESTES"
    echo ""
    echo "❌ Alguns testes falharam. Verifique os logs acima."
    echo ""
    echo "Para ver logs de um módulo específico:"
    echo "  docker-compose -f $DOCKER_COMPOSE_FILE logs <module>"
    echo ""
    echo "Para parar todos os serviços:"
    echo "  docker-compose -f $DOCKER_COMPOSE_FILE down"
    exit 1
fi

