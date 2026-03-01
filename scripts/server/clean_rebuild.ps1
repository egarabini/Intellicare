# Script to connect to server and execute clean rebuild
$SERVER = "167.86.97.142"
$USER = "root"
$PASSWORD = "Soeuso410863"
$LOCAL_PATH = "C:\DOCSHARE\INTELLICARE"

Write-Host "============================================================================" -ForegroundColor Red
Write-Host "⚠️  CLEAN AND REBUILD FROM SCRATCH" -ForegroundColor Red
Write-Host "============================================================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will DELETE EVERYTHING on the server and rebuild from scratch!" -ForegroundColor Yellow
Write-Host "ALL DATA WILL BE LOST!" -ForegroundColor Red
Write-Host ""

Write-Host "Server: $SERVER" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press ENTER to continue or Ctrl+C to cancel"

Write-Host ""
Write-Host "Step 1: Prepare local repository" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow
Set-Location $LOCAL_PATH
Write-Host "Current directory: $LOCAL_PATH" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Upload clean script to server" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

$plink = Get-Command plink -ErrorAction SilentlyContinue
$pscp = Get-Command pscp -ErrorAction SilentlyContinue

if (-not $plink -or -not $pscp) {
    Write-Host "ERROR: PuTTY not found. Please install from https://www.putty.org/" -ForegroundColor Red
    exit 1
}

# Upload the script
$scriptPath = "$LOCAL_PATH\scripts\server\clean_and_rebuild.sh"
if (Test-Path $scriptPath) {
    echo y | & $pscp.Path -pw $PASSWORD $scriptPath "$USER@$SERVER`:/tmp/"
    Write-Host "Script uploaded" -ForegroundColor Green
} else {
    Write-Host "ERROR: Script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host ""

Write-Host "Step 3: Execute clean and rebuild" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Yellow
Write-Host "This will take 15-30 minutes..." -ForegroundColor Cyan
Write-Host ""

# Execute the script
$output = echo y | & $plink.Path -ssh -pw $PASSWORD "$USER@$SERVER" "bash /tmp/clean_and_rebuild.sh" 2>&1

Write-Host $output

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "DONE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To connect to the server and check status:" -ForegroundColor Cyan
Write-Host "  plink -ssh -pw $PASSWORD $USER@$SERVER" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  docker ps                    # List containers" -ForegroundColor White
Write-Host "  docker logs <name> --tail 50 # View logs" -ForegroundColor White
Write-Host "  docker stats                 # Resource usage" -ForegroundColor White
Write-Host ""
