# Deploy apresentacao.intellicare.ia.br
# Uso: powershell -ExecutionPolicy Bypass -File deploy_apresentacao_simples.ps1

$SERVER = "root@167.86.97.142"

Write-Host "Deploy: apresentacao.intellicare.ia.br" -ForegroundColor Cyan
Write-Host ""

# Passo 1: Remover arquivo conflitante
Write-Host "Passo 1: Removendo arquivo conflitante..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare; rm -f traefik/dynamic/routes-intellicare.yml"
Write-Host ""

# Passo 2: Git pull
Write-Host "Passo 2: Git pull..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare; git pull origin master"
Write-Host ""

# Passo 3: Docker compose up
Write-Host "Passo 3: Iniciando container..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare/intellicare-apresentacao; docker-compose up -d"
Write-Host ""

# Passo 4: Verificar
Write-Host "Passo 4: Verificando container..." -ForegroundColor Yellow
ssh $SERVER "docker ps --filter name=apresentacao"
Write-Host ""

# Passo 5: Aguardar SSL
Write-Host "Passo 5: Aguardando certificado SSL (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Passo 6: Testar
Write-Host "Passo 6: Testando endpoint..." -ForegroundColor Yellow
curl -Ik https://apresentacao.intellicare.ia.br 2>&1 | Select-String -Pattern "HTTP" | Select-Object -First 1

Write-Host ""
Write-Host "Deploy concluido! Acesse: https://apresentacao.intellicare.ia.br" -ForegroundColor Green

