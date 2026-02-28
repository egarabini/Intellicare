#!/bin/bash
# Script para executar diferentes cenários de benchmark do HL7v2 endpoint
# Target: 1000+ mensagens por segundo

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
URL="${HL7V2_URL:-http://localhost:8012/api/v1/hl7v2/adt-a04}"
API_KEY="${HL7V2_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Erro: HL7V2_API_KEY não configurada!${NC}"
    echo "Configure a variável de ambiente:"
    echo "  export HL7V2_API_KEY=<sua_api_key>"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         HL7v2 Performance Benchmark Suite                     ║${NC}"
echo -e "${BLUE}║         Target: 1000+ mensagens por segundo                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}URL:${NC} $URL"
echo -e "${YELLOW}API Key:${NC} ${API_KEY:0:10}..."
echo ""

# Criar diretório para resultados
RESULTS_DIR="benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"
echo -e "${GREEN}📁 Resultados serão salvos em: $RESULTS_DIR${NC}"
echo ""

# Função para executar benchmark
run_benchmark() {
    local name=$1
    local requests=$2
    local concurrency=$3
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🚀 Cenário: $name${NC}"
    echo -e "${YELLOW}   Requisições: $requests | Concorrência: $concurrency${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    python scripts/benchmark_hl7v2.py \
        --url "$URL" \
        --api-key "$API_KEY" \
        --requests "$requests" \
        --concurrency "$concurrency" \
        | tee "$RESULTS_DIR/${name}.txt"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ $name: TARGET ATINGIDO!${NC}"
    else
        echo -e "${RED}⚠️  $name: Abaixo do target${NC}"
    fi
    
    echo ""
    sleep 5  # Pausa entre cenários
}

# Cenário 1: Warmup (baixa carga)
run_benchmark "01_warmup" 1000 10

# Cenário 2: Carga baixa
run_benchmark "02_low_load" 5000 50

# Cenário 3: Carga média
run_benchmark "03_medium_load" 10000 100

# Cenário 4: Carga alta (target: 1000 req/s)
run_benchmark "04_high_load" 20000 200

# Cenário 5: Stress test (acima do target)
run_benchmark "05_stress_test" 50000 500

# Cenário 6: Spike test (pico de carga)
run_benchmark "06_spike_test" 100000 1000

# Resumo final
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RESUMO DOS BENCHMARKS                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extrair RPS de cada cenário
for file in "$RESULTS_DIR"/*.txt; do
    scenario=$(basename "$file" .txt)
    rps=$(grep "Requisições/segundo:" "$file" | awk '{print $2}')
    
    if [ -n "$rps" ]; then
        # Comparar com target
        if (( $(echo "$rps >= 1000" | bc -l) )); then
            echo -e "${GREEN}✅ $scenario: $rps req/s${NC}"
        else
            echo -e "${YELLOW}⚠️  $scenario: $rps req/s${NC}"
        fi
    fi
done

echo ""
echo -e "${GREEN}📊 Resultados completos salvos em: $RESULTS_DIR${NC}"
echo ""

# Gerar relatório consolidado
cat > "$RESULTS_DIR/SUMMARY.md" << EOF
# HL7v2 Performance Benchmark - Resumo

**Data:** $(date)
**URL:** $URL
**Target:** 1000+ req/s

## Cenários Executados

EOF

for file in "$RESULTS_DIR"/*.txt; do
    scenario=$(basename "$file" .txt)
    echo "### $scenario" >> "$RESULTS_DIR/SUMMARY.md"
    echo '```' >> "$RESULTS_DIR/SUMMARY.md"
    grep -A 20 "RESULTADOS DO BENCHMARK" "$file" >> "$RESULTS_DIR/SUMMARY.md" || true
    echo '```' >> "$RESULTS_DIR/SUMMARY.md"
    echo "" >> "$RESULTS_DIR/SUMMARY.md"
done

echo -e "${GREEN}✅ Relatório consolidado: $RESULTS_DIR/SUMMARY.md${NC}"

