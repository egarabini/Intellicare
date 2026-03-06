param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("portal", "admin", "keycloak")]
    [string]$Module,

    [Parameter(Mandatory = $true)]
    [string]$Host,

    [string]$User = "root",
    [string]$Branch = "main",
    [string]$RepoPath = "/opt/intellicare",
    [string]$ComposeFile = "docker-compose.full.yml",
    [string]$EnvFile = ".env.full",
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$serviceMap = @{
    "portal"   = @{
        Service   = "portal"
        HealthUrl = "http://localhost:3001"
    }
    "admin"    = @{
        Service   = "admin"
        HealthUrl = "http://localhost:8010/api/v1/health"
    }
    "keycloak" = @{
        Service   = "keycloak"
        HealthUrl = "http://localhost:8080/health/ready"
    }
}

if (-not $serviceMap.ContainsKey($Module)) {
    throw "Unsupported module: $Module"
}

$service = $serviceMap[$Module].Service
$healthUrl = $serviceMap[$Module].HealthUrl
$buildFlag = ""
if ($Build) {
    $buildFlag = "--build"
}

$remoteScript = @"
set -euo pipefail

cd "$RepoPath"

echo "[1/5] Sync git branch $Branch"
git fetch --all --prune
git checkout "$Branch"
git pull --ff-only origin "$Branch"

echo "[2/5] Pull latest image for service $service"
docker compose --env-file "$EnvFile" -f "$ComposeFile" pull "$service"

echo "[3/5] Start service $service"
docker compose --env-file "$EnvFile" -f "$ComposeFile" up -d $buildFlag "$service"

echo "[4/5] Service status"
docker compose --env-file "$EnvFile" -f "$ComposeFile" ps "$service"

echo "[5/5] Health check"
if command -v curl >/dev/null 2>&1; then
  curl -fsS "$healthUrl" >/dev/null
  echo "Health check passed: $healthUrl"
else
  echo "curl not found; skipping health HTTP check"
fi
"@

$target = "$User@$Host"
$remoteScript | ssh $target "bash -s"

Write-Host "Deploy completed for module '$Module' on '$target'."
