param(
    [Parameter(Mandatory = $true)]
    [string]$Host,
    [string]$User = "root",
    [string]$Branch = "main",
    [string]$RepoPath = "/opt/intellicare/MODULARIZACAO",
    [string]$ComposeFile = "docker-compose.full.yml",
    [string]$EnvFile = ".env.full",
    [switch]$Build
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptDir "deploy-module.ps1"

& $runner -Module "admin" -Host $Host -User $User -Branch $Branch -RepoPath $RepoPath -ComposeFile $ComposeFile -EnvFile $EnvFile -Build:$Build
