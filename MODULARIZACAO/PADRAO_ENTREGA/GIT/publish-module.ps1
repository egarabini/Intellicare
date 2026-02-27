param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("portal", "admin")]
    [string]$Module,

    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,

    [string]$Branch = "main",

    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")

$moduleConfig = @{
    "portal" = @{
        Path = "intellicare-portal"
        ValidateCommand = @("npm", "--prefix", "intellicare-portal/frontend", "run", "build")
    }
    "admin" = @{
        Path = "intellicare-admin"
        ValidateCommand = @("python", "-m", "pytest", "-q")
        ValidateWorkdir = "intellicare-admin"
    }
}

function Invoke-CheckedCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$Workdir
    )

    if ($Workdir) {
        Push-Location (Join-Path $repoRoot $Workdir)
    } else {
        Push-Location $repoRoot
    }

    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed: $Command $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not $moduleConfig.ContainsKey($Module)) {
    throw "Unsupported module: $Module"
}

$config = $moduleConfig[$Module]
$modulePath = $config.Path

Push-Location $repoRoot
try {
    $changes = git status --porcelain -- $modulePath
    if (-not $changes) {
        Write-Host "No local changes found for module '$Module' ($modulePath)."
        exit 0
    }

    if (-not $SkipValidation) {
        $validateCommand = $config.ValidateCommand
        if ($null -ne $validateCommand) {
            $validateExe = $validateCommand[0]
            $validateArgs = @()
            if ($validateCommand.Count -gt 1) {
                $validateArgs = $validateCommand[1..($validateCommand.Count - 1)]
            }
            $validateWorkdir = $config.ValidateWorkdir
            Write-Host "Running validation for module '$Module'..."
            Invoke-CheckedCommand -Command $validateExe -Arguments $validateArgs -Workdir $validateWorkdir
        }
    }

    git add -- $modulePath
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed"
    }

    git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed"
    }

    git push origin "HEAD:$Branch"
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed"
    }

    Write-Host "Publish completed for module '$Module' on branch '$Branch'."
}
finally {
    Pop-Location
}
