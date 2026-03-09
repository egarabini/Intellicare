#!/bin/bash
# Script para corrigir URL encoding de senhas no .env
# Data: 2026-02-22
# Problema: Caracteres especiais (@ e !) na senha não estavam URL-encoded

set -e

echo "🔧 Corrigindo URL encoding de senhas no .env..."

# Backup do .env
cp .env .env.backup.url-encode.$(date +%Y%m%d-%H%M%S)
echo "✅ Backup criado"

# Aplicar URL encoding
# @ → %40
# ! → %21
sed -i 's|IntelliCare@Homolog2026!Pg|IntelliCare%40Homolog2026%21Pg|g' .env

echo "✅ URL encoding aplicado"

# Verificar mudanças
echo ""
echo "📋 Verificando DATABASE_URLs:"
grep "DATABASE_URL" .env | grep -v "^#"

echo ""
echo "🔄 Reiniciando containers Oswaldo e Comunicacao..."
docker-compose -f docker-compose.full.yml restart oswaldo comunicacao

echo ""
echo "⏳ Aguardando 30 segundos para containers iniciarem..."
sleep 30

echo ""
echo "📊 Status dos containers:"
docker-compose -f docker-compose.full.yml ps | grep -E "(oswaldo|comunicacao|donabedian)"

echo ""
echo "📝 Logs do Oswaldo (últimas 10 linhas):"
docker logs intellicare-oswaldo --tail 10

echo ""
echo "✅ Correção concluída!"

