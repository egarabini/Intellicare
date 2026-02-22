# Script para fazer push da MODULARIZACAO para GitHub
# Execute este script no PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PUSH MODULARIZACAO PARA GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretório
Set-Location C:\DOCSHARE\INTELLICARE

# Verificar status
Write-Host "1. Verificando status do Git..." -ForegroundColor Yellow
git status

# Pull das alterações remotas
Write-Host ""
Write-Host "2. Fazendo pull das alterações remotas..." -ForegroundColor Yellow
git pull origin master --allow-unrelated-histories --no-edit

# Push das alterações locais
Write-Host ""
Write-Host "3. Fazendo push das alterações locais..." -ForegroundColor Yellow
git push -u origin main:master

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "CONCLUÍDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

