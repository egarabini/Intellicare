param(
    [Parameter(Mandatory = $true)]
    [string]$Host,
    [string]$User = "root",
    [string]$Branch = "main",
    [string]$RepoPath = "/opt/intellicare",
    [string]$ComposeFile = "docker-compose.keycloak.yml",
    [string]$EnvFile = ".env.keycloak",
    [switch]$Build
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptDir "deploy-module.ps1"

& $runner -Module "keycloak" -Host $Host -User $User -Branch $Branch -RepoPath $RepoPath -ComposeFile $ComposeFile -EnvFile $EnvFile -Build:$Build
