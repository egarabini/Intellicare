param(
    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,
    [string]$Branch = "main",
    [switch]$SkipValidation
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptDir "publish-module.ps1"

& $runner -Module "admin" -CommitMessage $CommitMessage -Branch $Branch -SkipValidation:$SkipValidation
