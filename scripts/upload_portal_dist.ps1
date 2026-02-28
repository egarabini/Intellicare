# Upload Portal Dist to Server
# This script uploads the built portal files to the server

$SERVER = "root@167.86.97.142"
$LOCAL_DIST = ".\intellicare-portal\frontend\dist"

Write-Host "Uploading Portal Dist to Server..." -ForegroundColor Blue
Write-Host ""

# Create remote directory
Write-Host "Creating remote directory..." -ForegroundColor Cyan
ssh $SERVER 'mkdir -p /opt/intellicare/portal-dist'
ssh $SERVER 'rm -rf /opt/intellicare/portal-dist/*'

# Upload files
Write-Host "Uploading files..." -ForegroundColor Cyan
scp -r "$LOCAL_DIST\*" "${SERVER}:/opt/intellicare/portal-dist/"

Write-Host ""
Write-Host "Upload complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying files on server..." -ForegroundColor Cyan
ssh $SERVER 'ls -lah /opt/intellicare/portal-dist'

