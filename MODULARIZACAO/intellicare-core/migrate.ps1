# PowerShell Migration Runner for IntelliCare
# Apply Alembic migrations to IntelliCare database
# 
# Usage:
#   .\migrate.ps1 upgrade              # Apply all migrations
#   .\migrate.ps1 upgrade -Revision 003 # Apply up to migration 003
#   .\migrate.ps1 downgrade -Revision 001 # Revert to migration 001
#   .\migrate.ps1 current              # Show current revision

param(
    [Parameter(Position = 0)]
    [ValidateSet('upgrade', 'downgrade', 'current', 'history', 'revision', 'heads', 'branches')]
    [string]$Command = 'upgrade',
    
    [Parameter()]
    [string]$Revision = 'head',
    
    [Parameter()]
    [string]$Message = '',
    
    [Parameter()]
    [string]$DatabaseUrl = $env:DATABASE_URL
)

# Set defaults
if (-not $DatabaseUrl) {
    $DatabaseUrl = 'postgresql://intellicare_admin:CHANGE_ME@localhost:5432/intellicare_db'
}

# Colors
$Green = 'Green'
$Yellow = 'Yellow'
$Red = 'Red'

Write-Host "IntelliCare Migration Runner" -ForegroundColor $Yellow
Write-Host "=============================" -ForegroundColor $Yellow
Write-Host "Database: $DatabaseUrl"
Write-Host "Command: $Command"
if ($Revision -ne 'head') { Write-Host "Revision: $Revision" }
Write-Host ""

# Helper function
function Invoke-Alembic {
    param([string]$Arguments)
    
    $env:DATABASE_URL = $DatabaseUrl
    $output = & python -m alembic $Arguments
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Operation successful" -ForegroundColor $Green
        return $true
    }
    else {
        Write-Host "❌ Operation failed" -ForegroundColor $Red
        Write-Host $output
        exit 1
    }
}

# Main logic
switch ($Command) {
    'upgrade' {
        Write-Host "🚀 Applying migrations up to revision: $Revision"
        & python -m alembic upgrade $Revision
    }
    
    'downgrade' {
        Write-Host "⬇️ Reverting migrations to revision: $Revision"
        & python -m alembic downgrade $Revision
    }
    
    'current' {
        Write-Host "📍 Current database revision:"
        & python -m alembic current
    }
    
    'history' {
        Write-Host "📜 Migration history:"
        & python -m alembic history --verbose
    }
    
    'revision' {
        if (-not $Message) {
            Write-Host "❌ Message required for new migration" -ForegroundColor $Red
            Write-Host "Usage: .\migrate.ps1 revision -Message 'Your migration description'"
            exit 1
        }
        Write-Host "📝 Creating new migration: $Message"
        & python -m alembic revision --autogenerate -m "$Message"
    }
    
    'heads' {
        Write-Host "🎯 Current migration heads:"
        & python -m alembic heads
    }
    
    'branches' {
        Write-Host "🌳 Migration branches:"
        & python -m alembic branches
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Done! 🎉" -ForegroundColor $Green
}
else {
    exit 1
}

