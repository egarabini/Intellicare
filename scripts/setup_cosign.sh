#!/bin/bash
# Setup e validação de image signing com cosign para W8-D Production Hardening

set -e

echo "=========================================="
echo "🔐 COSIGN IMAGE SIGNING SETUP - W8-D"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variáveis
COSIGN_VERSION="v2.2.3"
KEY_DIR="$HOME/.cosign"
PRIVATE_KEY="$KEY_DIR/cosign.key"
PUBLIC_KEY="$KEY_DIR/cosign.pub"
REGISTRY="${REGISTRY:-ghcr.io/intellicare}"

# Função para print colorido
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 1. Verificar se cosign está instalado
echo ""
echo "1️⃣  Verificando instalação do cosign..."
if command -v cosign &> /dev/null; then
    INSTALLED_VERSION=$(cosign version 2>&1 | grep GitVersion | awk '{print $2}')
    print_success "Cosign já instalado: $INSTALLED_VERSION"
else
    print_info "Cosign não encontrado. Instalando versão $COSIGN_VERSION..."
    
    # Detectar OS
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    fi
    
    # Download cosign
    COSIGN_URL="https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-${OS}-${ARCH}"
    
    curl -L -o /tmp/cosign "$COSIGN_URL"
    chmod +x /tmp/cosign
    sudo mv /tmp/cosign /usr/local/bin/cosign
    
    print_success "Cosign instalado com sucesso"
fi

# 2. Criar diretório para chaves
echo ""
echo "2️⃣  Configurando diretório de chaves..."
mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"
print_success "Diretório criado: $KEY_DIR"

# 3. Gerar par de chaves (se não existir)
echo ""
echo "3️⃣  Gerando par de chaves..."
if [ -f "$PRIVATE_KEY" ] && [ -f "$PUBLIC_KEY" ]; then
    print_info "Chaves já existem. Pulando geração."
else
    print_info "Gerando novo par de chaves..."
    
    # Gerar chaves sem senha (para CI/CD)
    # Em produção, use senha e armazene em secret manager
    COSIGN_PASSWORD="" cosign generate-key-pair --output-key-prefix="$KEY_DIR/cosign"
    
    chmod 600 "$PRIVATE_KEY"
    chmod 644 "$PUBLIC_KEY"
    
    print_success "Par de chaves gerado:"
    print_info "  Privada: $PRIVATE_KEY"
    print_info "  Pública: $PUBLIC_KEY"
fi

# 4. Exibir chave pública
echo ""
echo "4️⃣  Chave pública (para distribuição):"
echo "----------------------------------------"
cat "$PUBLIC_KEY"
echo "----------------------------------------"

# 5. Testar assinatura de imagem
echo ""
echo "5️⃣  Testando assinatura de imagem..."

# Escolher uma imagem de teste
TEST_IMAGE="${REGISTRY}/intellicare-grahame:latest"

print_info "Imagem de teste: $TEST_IMAGE"

# Verificar se imagem existe localmente
if docker image inspect "$TEST_IMAGE" &> /dev/null; then
    print_success "Imagem encontrada localmente"
    
    # Assinar imagem
    print_info "Assinando imagem..."
    COSIGN_PASSWORD="" cosign sign --key "$PRIVATE_KEY" "$TEST_IMAGE" --yes
    
    print_success "Imagem assinada com sucesso"
    
    # Verificar assinatura
    print_info "Verificando assinatura..."
    if cosign verify --key "$PUBLIC_KEY" "$TEST_IMAGE"; then
        print_success "Assinatura verificada com sucesso!"
    else
        print_error "Falha ao verificar assinatura"
        exit 1
    fi
else
    print_info "Imagem de teste não encontrada localmente. Pulando teste de assinatura."
    print_info "Execute 'docker pull $TEST_IMAGE' ou 'docker build' primeiro."
fi

# 6. Criar script de assinatura em lote
echo ""
echo "6️⃣  Criando script de assinatura em lote..."

cat > "$KEY_DIR/sign_all_images.sh" << 'EOF'
#!/bin/bash
# Script para assinar todas as imagens IntelliCare

set -e

REGISTRY="${REGISTRY:-ghcr.io/intellicare}"
KEY_DIR="$HOME/.cosign"
PRIVATE_KEY="$KEY_DIR/cosign.key"

MODULES=(
    "intellicare-grahame"
    "intellicare-oswaldo"
    "intellicare-florence"
    "intellicare-wanda"
    "intellicare-donabedian"
    "intellicare-zilda"
    "intellicare-geralda"
    "intellicare-comunicacao"
    "intellicare-core"
)

echo "🔐 Assinando todas as imagens IntelliCare..."

for module in "${MODULES[@]}"; do
    IMAGE="${REGISTRY}/${module}:latest"
    echo ""
    echo "Assinando: $IMAGE"
    
    if docker image inspect "$IMAGE" &> /dev/null; then
        COSIGN_PASSWORD="" cosign sign --key "$PRIVATE_KEY" "$IMAGE" --yes
        echo "✅ $module assinado"
    else
        echo "⚠️  $module não encontrado localmente. Pulando."
    fi
done

echo ""
echo "🎉 Assinatura em lote concluída!"
EOF

chmod +x "$KEY_DIR/sign_all_images.sh"
print_success "Script criado: $KEY_DIR/sign_all_images.sh"

# 7. Criar script de verificação em lote
echo ""
echo "7️⃣  Criando script de verificação em lote..."

cat > "$KEY_DIR/verify_all_images.sh" << 'EOF'
#!/bin/bash
# Script para verificar assinaturas de todas as imagens IntelliCare

set -e

REGISTRY="${REGISTRY:-ghcr.io/intellicare}"
KEY_DIR="$HOME/.cosign"
PUBLIC_KEY="$KEY_DIR/cosign.pub"

MODULES=(
    "intellicare-grahame"
    "intellicare-oswaldo"
    "intellicare-florence"
    "intellicare-wanda"
    "intellicare-donabedian"
    "intellicare-zilda"
    "intellicare-geralda"
    "intellicare-comunicacao"
    "intellicare-core"
)

echo "🔍 Verificando assinaturas de todas as imagens IntelliCare..."

VERIFIED=0
FAILED=0

for module in "${MODULES[@]}"; do
    IMAGE="${REGISTRY}/${module}:latest"
    echo ""
    echo "Verificando: $IMAGE"
    
    if cosign verify --key "$PUBLIC_KEY" "$IMAGE" &> /dev/null; then
        echo "✅ $module verificado"
        ((VERIFIED++))
    else
        echo "❌ $module falhou na verificação"
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "📊 RELATÓRIO DE VERIFICAÇÃO"
echo "=========================================="
echo "✅ Verificadas: $VERIFIED"
echo "❌ Falhadas: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 TODAS AS IMAGENS VERIFICADAS COM SUCESSO!"
    exit 0
else
    echo ""
    echo "❌ ALGUMAS IMAGENS FALHARAM NA VERIFICAÇÃO"
    exit 1
fi
EOF

chmod +x "$KEY_DIR/verify_all_images.sh"
print_success "Script criado: $KEY_DIR/verify_all_images.sh"

# 8. Instruções finais
echo ""
echo "=========================================="
echo "📋 PRÓXIMOS PASSOS"
echo "=========================================="
echo ""
echo "1. Assinar todas as imagens:"
echo "   $KEY_DIR/sign_all_images.sh"
echo ""
echo "2. Verificar todas as assinaturas:"
echo "   $KEY_DIR/verify_all_images.sh"
echo ""
echo "3. Adicionar chave pública ao CI/CD:"
echo "   - GitHub Secrets: COSIGN_PUBLIC_KEY"
echo "   - Valor: conteúdo de $PUBLIC_KEY"
echo ""
echo "4. Adicionar chave privada ao CI/CD (CUIDADO!):"
echo "   - GitHub Secrets: COSIGN_PRIVATE_KEY"
echo "   - Valor: conteúdo de $PRIVATE_KEY"
echo ""
echo "5. Distribuir chave pública para verificação:"
echo "   - Documentação"
echo "   - README.md"
echo "   - Site público"
echo ""
print_success "Setup do cosign concluído com sucesso!"

