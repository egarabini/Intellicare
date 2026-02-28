# ============================================================================
# Deploy IntelliCare Apresentação - PowerShell Script
# ============================================================================

$ErrorActionPreference = "Continue"
$SERVER = "root@167.86.97.142"

Write-Host "🚀 Deploying IntelliCare Apresentação..." -ForegroundColor Cyan

# 1. Upload fix script
Write-Host "`n📤 Uploading fix script..." -ForegroundColor Yellow
scp .\scripts\fix_apresentacao.sh ${SERVER}:/tmp/

# 2. Upload Traefik config
Write-Host "`n📤 Uploading Traefik configuration..." -ForegroundColor Yellow
scp .\traefik\dynamic\routes-intellicare.yml ${SERVER}:/opt/intellicare/intellicare/traefik/dynamic/

# 3. Execute fix script
Write-Host "`n🔧 Executing fix script on server..." -ForegroundColor Yellow
ssh $SERVER "bash /tmp/fix_apresentacao.sh"

# 4. Wait and test
Write-Host "`n⏳ Waiting for Let's Encrypt..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "`n🧪 Testing endpoint..." -ForegroundColor Yellow
curl -Ik https://apresentacao.intellicare.ia.br 2>&1 | Select-String -Pattern "HTTP|Content-Type" | Select-Object -First 3

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✅ IntelliCare Apresentação Deployed!                  ║" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "║   🌐 https://apresentacao.intellicare.ia.br              ║" -ForegroundColor Green
Write-Host "║   📊 Reveal.js Slides                                    ║" -ForegroundColor Green
Write-Host "║   🔐 HTTPS: Let's Encrypt (auto)                         ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

