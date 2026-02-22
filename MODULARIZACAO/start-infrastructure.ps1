# ============================================================================
# IntelliCare STEP 1.4 - Infrastructure Startup Script (Windows PowerShell)
# ============================================================================
# Starts PostgreSQL, Redis, Prometheus, and Grafana containers
# Usage: .\start-infrastructure.ps1 [command]
# Commands: Up, Down, Logs, Status, Clean, Connections
# ============================================================================

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('Up', 'Down', 'Logs', 'Status', 'Clean', 'Connections', 'Help')]
    [string]$Command = 'Up'
)

$ErrorActionPreference = 'Stop'

# Colors
$SUCCESS = 'Green'
$ERROR_COLOR = 'Red'
$WARNING = 'Yellow'
$INFO = 'Cyan'

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir 'docker-compose.yml'
$ProjectName = 'intellicare-phase1.4'

# ============================================================================
# Utility Functions
# ============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $INFO
    Write-Host $Text -ForegroundColor $INFO
    Write-Host "========================================" -ForegroundColor $INFO
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $SUCCESS
}

function Write-ErrorMsg {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $ERROR_COLOR
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor $WARNING
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor $INFO
}

# ============================================================================
# Main Functions
# ============================================================================

function Start-InfrastructureAppliance {
    Write-Header "Starting IntelliCare Infrastructure"
    
    # Check if Docker is running
    try {
        $null = docker info 2>$null
    }
    catch {
        Write-ErrorMsg "Docker is not running. Please start Docker first."
        exit 1
    }
    
    Write-Info "Pulling latest images..."
    docker-compose -f $ComposeFile -p $ProjectName pull
    
    Write-Info "Starting services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d
    
    Write-Success "Infrastructure started!"
    Write-Info "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    Write-Info "Waiting for PostgreSQL..."
    $timeout = 0
    while ($timeout -lt 30) {
        try {
            $result = docker-compose -f $ComposeFile -p $ProjectName exec -T postgres pg_isready -U intellicare_admin 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "PostgreSQL is ready!"
                break
            }
        }
        catch {
            # Still waiting
        }
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 1
        $timeout++
    }
    
    # Wait for Redis
    Write-Info "Waiting for Redis..."
    $timeout = 0
    while ($timeout -lt 30) {
        try {
            $result = docker-compose -f $ComposeFile -p $ProjectName exec -T redis redis-cli ping 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Redis is ready!"
                break
            }
        }
        catch {
            # Still waiting
        }
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 1
        $timeout++
    }
    
    # Wait for other services
    Start-Sleep -Seconds 3
    Write-Success "Prometheus is ready!"
    
    # Display connection information
    Write-Header "Connection Information"
    Write-Host "PostgreSQL:  " -ForegroundColor $INFO -NoNewline
    Write-Host "postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db" -ForegroundColor $SUCCESS
    
    Write-Host "Redis:       " -ForegroundColor $INFO -NoNewline
    Write-Host "redis://localhost:6379" -ForegroundColor $SUCCESS
    
    Write-Host "Prometheus:  " -ForegroundColor $INFO -NoNewline
    Write-Host "http://localhost:9090" -ForegroundColor $SUCCESS
    
    Write-Host "Grafana:     " -ForegroundColor $INFO -NoNewline
    Write-Host "http://localhost:3000" -ForegroundColor $SUCCESS
    Write-Host "(admin/intellicare_grafana)" -ForegroundColor $WARNING
    
    Write-Info "Running initial setup..."
    Setup-RedisConsumerGroups
    Verify-Database
}

function Stop-InfrastructureAppliance {
    Write-Header "Stopping IntelliCare Infrastructure"
    
    docker-compose -f $ComposeFile -p $ProjectName down
    
    Write-Success "Infrastructure stopped!"
}

function Show-Logs {
    Write-Header "Infrastructure Logs"
    docker-compose -f $ComposeFile -p $ProjectName logs -f
}

function Show-Status {
    Write-Header "Infrastructure Status"
    docker-compose -f $ComposeFile -p $ProjectName ps
    
    Write-Host ""
    Write-Info "Service Health:"
    
    # PostgreSQL
    try {
        $null = docker-compose -f $ComposeFile -p $ProjectName exec -T postgres pg_isready -U intellicare_admin 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL: UP"
        }
        else {
            Write-ErrorMsg "PostgreSQL: DOWN"
        }
    }
    catch {
        Write-ErrorMsg "PostgreSQL: DOWN"
    }
    
    # Redis
    try {
        $null = docker-compose -f $ComposeFile -p $ProjectName exec -T redis redis-cli ping 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Redis: UP"
        }
        else {
            Write-ErrorMsg "Redis: DOWN"
        }
    }
    catch {
        Write-ErrorMsg "Redis: DOWN"
    }
    
    # Prometheus
    try {
        $null = Invoke-WebRequest -Uri 'http://localhost:9090/-/healthy' -UseBasicParsing 2>$null
        Write-Success "Prometheus: UP"
    }
    catch {
        Write-ErrorMsg "Prometheus: DOWN"
    }
    
    # Grafana
    try {
        $null = Invoke-WebRequest -Uri 'http://localhost:3000/api/health' -UseBasicParsing 2>$null
        Write-Success "Grafana: UP"
    }
    catch {
        Write-ErrorMsg "Grafana: DOWN"
    }
}

function Clean-InfrastructureAppliance {
    Write-Header "Cleaning Infrastructure"
    Write-Warning "This will remove all containers, volumes, and data!"
    
    $response = Read-Host "Are you sure? (yes/no)"
    
    if ($response -eq 'yes') {
        docker-compose -f $ComposeFile -p $ProjectName down -v
        Write-Success "Infrastructure cleaned!"
    }
    else {
        Write-Info "Cleanup cancelled."
    }
}

function Setup-RedisConsumerGroups {
    Write-Info "Setting up Redis consumer groups..."
    
    try {
        $null = docker-compose -f $ComposeFile -p $ProjectName exec -T redis redis-cli XGROUP CREATE consolidation consolidation-events $ MKSTREAM 2>$null
        Write-Success "Consumer group 'consolidation' created"
    }
    catch {
        Write-Warning "Consumer group already exists or Redis not ready"
    }
}

function Verify-Database {
    Write-Info "Verifying database setup..."
    
    try {
        $schemas = docker-compose -f $ComposeFile -p $ProjectName exec -T postgres `
            psql -U intellicare_admin -d intellicare_db -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE '%operacional';" 2>$null | Select-String -Pattern "\d+" | Select-Object -First 1
        
        if ($schemas -match '10') {
            Write-Success "Database schemas created correctly"
        }
        else {
            Write-Warning "Database schemas may not be initialized correctly"
        }
    }
    catch {
        Write-Warning "Could not verify database"
    }
}

function Show-ConnectionStrings {
    Write-Header "Connection Strings"
    
    Write-Host "PostgreSQL (psql):" -ForegroundColor $INFO
    Write-Host "  psql -h localhost -U intellicare_admin -d intellicare_db" -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Redis (redis-cli):" -ForegroundColor $INFO
    Write-Host "  redis-cli -h localhost -p 6379" -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Environment Variables (PowerShell):" -ForegroundColor $INFO
    Write-Host '$env:DATABASE_URL = "postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db"' -ForegroundColor $SUCCESS
    Write-Host '$env:REDIS_URL = "redis://localhost:6379"' -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Environment Variables (CMD):" -ForegroundColor $INFO
    Write-Host 'set DATABASE_URL=postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db' -ForegroundColor $SUCCESS
    Write-Host 'set REDIS_URL=redis://localhost:6379' -ForegroundColor $SUCCESS
    Write-Host ""
}

function Show-Help {
    Write-Header "IntelliCare STEP 1.4 - Infrastructure Startup Script"
    
    Write-Host "Usage: .\start-infrastructure.ps1 [command]" -ForegroundColor $INFO
    Write-Host ""
    
    Write-Host "Commands:" -ForegroundColor $INFO
    Write-Host "  Up          - Start all infrastructure containers (default)" -ForegroundColor $SUCCESS
    Write-Host "  Down        - Stop all containers" -ForegroundColor $SUCCESS
    Write-Host "  Logs        - Show container logs" -ForegroundColor $SUCCESS
    Write-Host "  Status      - Show container status" -ForegroundColor $SUCCESS
    Write-Host "  Clean       - Remove all containers and volumes (⚠️  destructive!)" -ForegroundColor $WARNING
    Write-Host "  Connections - Show connection strings" -ForegroundColor $SUCCESS
    Write-Host "  Help        - Show this help message" -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Examples:" -ForegroundColor $INFO
    Write-Host "  .\start-infrastructure.ps1 Up" -ForegroundColor $SUCCESS
    Write-Host "  .\start-infrastructure.ps1 Status" -ForegroundColor $SUCCESS
    Write-Host "  .\start-infrastructure.ps1 Logs" -ForegroundColor $SUCCESS
    Write-Host "  .\start-infrastructure.ps1 Down" -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Services Started:" -ForegroundColor $INFO
    Write-Host "  - PostgreSQL 15  (port 5432)" -ForegroundColor $SUCCESS
    Write-Host "  - Redis 7        (port 6379)" -ForegroundColor $SUCCESS
    Write-Host "  - Prometheus     (port 9090)" -ForegroundColor $SUCCESS
    Write-Host "  - Grafana        (port 3000)" -ForegroundColor $SUCCESS
    Write-Host ""
    
    Write-Host "Default Credentials:" -ForegroundColor $INFO
    Write-Host "  PostgreSQL: intellicare_admin / intellicare_dev_pwd" -ForegroundColor $SUCCESS
    Write-Host "  Grafana:    admin / intellicare_grafana" -ForegroundColor $SUCCESS
    Write-Host ""
}

# ============================================================================
# Main Script Logic
# ============================================================================

switch ($Command.ToLower()) {
    'up' { Start-InfrastructureAppliance }
    'down' { Stop-InfrastructureAppliance }
    'logs' { Show-Logs }
    'status' { Show-Status }
    'clean' { Clean-InfrastructureAppliance }
    'connections' { Show-ConnectionStrings }
    'help' { Show-Help }
    default { Show-Help }
}
