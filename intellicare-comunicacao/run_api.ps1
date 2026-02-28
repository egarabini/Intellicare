param(
    [int]$Port = 8010,
    [string]$Host = "0.0.0.0",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

.venv\Scripts\python.exe -m pip install -e ..\intellicare-core
.venv\Scripts\python.exe -m pip install -r requirements.txt

$cmd = "import uvicorn; uvicorn.run('comunicacao.api.app:create_app', factory=True, host='$Host', port=$Port, reload=$($Reload.IsPresent.ToString().ToLower()))"
.venv\Scripts\python.exe -c $cmd
