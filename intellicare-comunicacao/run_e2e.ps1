param(
    [string]$BaseUrl = "http://localhost:8010",
    [string]$RedisUrl = "redis://localhost:6379",
    [string]$StreamPrefix = "intellicare",
    [string]$AlertType = "alert.created",
    [string]$RoomId = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RoomId)) {
    throw "Informe -RoomId '!sala:matrix.gsi.srv.br'"
}

if (!(Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

.venv\Scripts\python.exe -m pip install -e ..\intellicare-core
.venv\Scripts\python.exe -m pip install -r requirements.txt

$env:INTELLICARE_ENABLE_E2E = "true"
$env:INTELLICARE_E2E_BASE_URL = $BaseUrl
$env:INTELLICARE_E2E_REDIS_URL = $RedisUrl
$env:INTELLICARE_E2E_STREAM_PREFIX = $StreamPrefix
$env:INTELLICARE_E2E_ALERT_TYPE = $AlertType
$env:INTELLICARE_E2E_ROOM_ID = $RoomId

.venv\Scripts\python.exe -m pytest -m e2e -q -p no:cacheprovider
