#!/bin/bash

# ============================================================================
# Script de Deploy - Roteamento de Domínios Raiz
# ============================================================================
# Autor: Augment Agent
# Data: 2026-02-26
# Versão: 1.0.0
#
# Uso:
#   ./scripts/deploy_root_domains.sh test    # Teste local
#   ./scripts/deploy_root_domains.sh deploy  # Deploy em staging/produção
#   ./scripts/deploy_root_domains.sh rollback # Rollback
# ============================================================================

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# FASE 1: Teste Local
# ============================================================================
test_local() {
    log_info "Iniciando teste local..."
    echo ""
    
    # 1. Verificar arquivo
    log_info "1/5 - Verificando arquivo de configuração..."
    if [ ! -f "traefik/dynamic/routes-root-domains.yml" ]; then
        log_error "Arquivo routes-root-domains.yml não encontrado!"
        exit 1
    fi
    log_success "Arquivo encontrado"
    echo ""
    
    # 2. Validar sintaxe YAML
    log_info "2/5 - Validando sintaxe YAML..."
    if command -v yamllint &> /dev/null; then
        yamllint traefik/dynamic/routes-root-domains.yml
        log_success "Sintaxe YAML válida"
    else
        log_warning "yamllint não instalado, pulando validação"
    fi
    echo ""
    
    # 3. Subir Traefik em modo dev
    log_info "3/5 - Subindo Traefik em modo dev..."
    docker compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml up -d traefik
    sleep 10
    log_success "Traefik iniciado"
    echo ""
    
    # 4. Verificar logs
    log_info "4/5 - Verificando logs do Traefik..."
    if docker logs intellicare-traefik 2>&1 | grep -q "Configuration loaded"; then
        log_success "Configuração carregada com sucesso"
    else
        log_error "Erro ao carregar configuração"
        docker logs intellicare-traefik --tail 50
        exit 1
    fi
    echo ""
    
    # 5. Verificar rotas no dashboard
    log_info "5/5 - Verificando rotas no dashboard..."
    if curl -s http://localhost:8080/api/http/routers | grep -q "root-intellicare"; then
        log_success "Rotas de domínio raiz encontradas"
    else
        log_warning "Rotas não encontradas (pode ser normal se Traefik ainda está carregando)"
    fi
    echo ""
    
    log_success "Teste local COMPLETO!"
    echo ""
    log_info "Dashboard Traefik: http://localhost:8080/dashboard/"
    echo ""
    log_warning "Para testar redirecionamentos localmente:"
    echo "  1. Adicione ao /etc/hosts:"
    echo "     127.0.0.1 intellicare.ia.br"
    echo "     127.0.0.1 portal.intellicare.ia.br"
    echo "  2. Teste: curl -I http://intellicare.ia.br"
    echo ""
    log_info "Para limpar: docker compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml down traefik"
}

# ============================================================================
# FASE 2: Deploy
# ============================================================================
deploy() {
    log_info "Iniciando deploy..."
    echo ""
    
    # Verificar se estamos no servidor
    if [ ! -d "/opt/intellicare" ]; then
        log_error "Este comando deve ser executado no servidor!"
        log_info "Use: ssh root@167.86.97.142"
        exit 1
    fi
    
    cd /opt/intellicare
    
    # 1. Criar backup
    log_info "1/7 - Criando backup..."
    BACKUP_DIR="/opt/intellicare/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r traefik/dynamic "$BACKUP_DIR/"
    log_success "Backup criado em: $BACKUP_DIR"
    echo ""
    
    # 2. Verificar DNS
    log_info "2/7 - Verificando DNS..."
    DNS_OK=true
    for domain in intellicare.ia.br www.intellicare.ia.br saudeconectada.com.br www.saudeconectada.com.br; do
        IP=$(dig +short "$domain" | head -1)
        if [ "$IP" == "167.86.97.142" ]; then
            log_success "$domain → $IP"
        else
            log_error "$domain → $IP (esperado: 167.86.97.142)"
            DNS_OK=false
        fi
    done
    
    if [ "$DNS_OK" = false ]; then
        log_error "DNS não configurado corretamente!"
        log_warning "Configure DNS antes de continuar"
        exit 1
    fi
    echo ""
    
    # 3. Verificar arquivo
    log_info "3/7 - Verificando arquivo de configuração..."
    if [ ! -f "traefik/dynamic/routes-root-domains.yml" ]; then
        log_error "Arquivo routes-root-domains.yml não encontrado!"
        log_info "Faça upload do arquivo primeiro"
        exit 1
    fi
    log_success "Arquivo encontrado"
    echo ""
    
    # 4. Validar sintaxe
    log_info "4/7 - Validando sintaxe YAML..."
    if command -v yamllint &> /dev/null; then
        yamllint traefik/dynamic/routes-root-domains.yml
        log_success "Sintaxe YAML válida"
    else
        log_warning "yamllint não instalado, pulando validação"
    fi
    echo ""
    
    # 5. Recarregar Traefik
    log_info "5/7 - Recarregando Traefik..."
    docker restart intellicare-traefik
    sleep 15
    log_success "Traefik reiniciado"
    echo ""
    
    # 6. Verificar logs
    log_info "6/7 - Verificando logs..."
    if docker logs intellicare-traefik 2>&1 | grep -q "Configuration loaded"; then
        log_success "Configuração carregada com sucesso"
    else
        log_error "Erro ao carregar configuração"
        docker logs intellicare-traefik --tail 50
        exit 1
    fi
    echo ""
    
    # 7. Testar redirecionamentos
    log_info "7/7 - Testando redirecionamentos..."
    TESTS_OK=true
    
    for domain in intellicare.ia.br www.intellicare.ia.br saudeconectada.com.br www.saudeconectada.com.br; do
        RESPONSE=$(curl -s -I "https://$domain" | head -1)
        if echo "$RESPONSE" | grep -q "301"; then
            log_success "$domain → 301 Redirect"
        else
            log_error "$domain → $RESPONSE"
            TESTS_OK=false
        fi
    done
    
    echo ""
    
    if [ "$TESTS_OK" = true ]; then
        log_success "Deploy COMPLETO! ✨"
        echo ""
        log_info "Backup disponível em: $BACKUP_DIR"
        log_info "Para rollback: ./scripts/deploy_root_domains.sh rollback"
    else
        log_error "Alguns testes falharam!"
        log_warning "Verifique os logs: docker logs intellicare-traefik"
        log_info "Para rollback: ./scripts/deploy_root_domains.sh rollback"
        exit 1
    fi
}

# ============================================================================
# FASE 3: Rollback
# ============================================================================
rollback() {
    log_warning "Iniciando rollback..."
    echo ""
    
    # Verificar se estamos no servidor
    if [ ! -d "/opt/intellicare" ]; then
        log_error "Este comando deve ser executado no servidor!"
        exit 1
    fi
    
    cd /opt/intellicare
    
    # Encontrar último backup
    BACKUP_DIR=$(ls -t /opt/intellicare/backups/ | head -1)
    
    if [ -z "$BACKUP_DIR" ]; then
        log_error "Nenhum backup encontrado!"
        exit 1
    fi
    
    log_info "Restaurando backup: $BACKUP_DIR"
    cp -r "/opt/intellicare/backups/$BACKUP_DIR/dynamic/"* traefik/dynamic/
    
    log_info "Reiniciando Traefik..."
    docker restart intellicare-traefik
    sleep 10
    
    log_success "Rollback COMPLETO!"
    log_info "Verifique: docker logs intellicare-traefik --tail 50"
}

# ============================================================================
# Main
# ============================================================================
case "${1:-}" in
    test)
        test_local
        ;;
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    *)
        echo "Uso: $0 {test|deploy|rollback}"
        echo ""
        echo "  test     - Teste local (não afeta produção)"
        echo "  deploy   - Deploy em staging/produção"
        echo "  rollback - Reverter para backup anterior"
        exit 1
        ;;
esac

