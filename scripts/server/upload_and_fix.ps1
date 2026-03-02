# Simple script to connect and fix the server
$SERVER = "167.86.97.142"
$USER = "root"
$PASSWORD = "Soeuso410863"

Write-Host "Connecting to server $SERVER..." -ForegroundColor Cyan

# Using plink from PuTTY
$plink = "plink"
$pscp = "pscp"

# Check if plink exists
if (-not (Get-Command $plink -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: plink not found. Please install PuTTY from https://www.putty.org/" -ForegroundColor Red
    exit 1
}

# Function to run SSH command
function Run-SSH {
    param([string]$Command)
    echo y | & $plink -ssh -pw $PASSWORD "$USER@$SERVER" $Command 2>&1
}

# Function to upload file
function Upload-File {
    param([string]$LocalPath, [string]$RemotePath)
    echo y | & $pscp -pw $PASSWORD $LocalPath "$USER@$SERVER`:$RemotePath" 2>&1
}

Write-Host ""
Write-Host "Step 1: Check connection" -ForegroundColor Yellow
$result = Run-SSH "echo 'Connection OK'"
Write-Host $result

Write-Host ""
Write-Host "Step 2: Check Docker version" -ForegroundColor Yellow
$result = Run-SSH "docker --version 2>&1 || echo 'Docker not working'"
Write-Host $result

Write-Host ""
Write-Host "Step 3: Upload fix script" -ForegroundColor Yellow
$scriptPath = "C:\DOCSHARE\INTELLICARE\scripts\server\fix_docker.sh"
if (Test-Path $scriptPath) {
    $result = Upload-File $scriptPath "/tmp/fix_docker.sh"
    Write-Host "Script uploaded"
    # Make it executable
    Run-SSH "chmod +x /tmp/fix_docker.sh"
} else {
    Write-Host "Script not found: $scriptPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "Step 4: Upload Traefik configs" -ForegroundColor Yellow
$baseDir = "C:\DOCSHARE\INTELLICARE"
Upload-File "$baseDir\traefik\dynamic\routes-intellicare.yml" "/opt/intellicare/intellicare/traefik/dynamic/"
Upload-File "$baseDir\traefik\dynamic\routes-saudeconectada.yml" "/opt/intellicare/intellicare/traefik/dynamic/"
Write-Host "Configs uploaded"

Write-Host ""
Write-Host "Step 5: Run fix script (press Ctrl+C to skip)" -ForegroundColor Yellow
Write-Host "This will update Docker on the server..." -ForegroundColor Yellow
Pause

Run-SSH "bash /tmp/fix_docker.sh"

Write-Host ""
Write-Host "Step 6: Check containers" -ForegroundColor Yellow
Start-Sleep -Seconds 5
$result = Run-SSH "docker ps --filter 'name=intellicare' --format 'table {{.Names}}\t{{.Status}}'"
Write-Host $result

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "To connect manually: plink -ssh -pw $PASSWORD $USER@$SERVER"
