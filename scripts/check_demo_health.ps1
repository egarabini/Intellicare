param(
    [int]$TimeoutSec = 5
)

$targets = @(
    @{ Name = "Florence"; Url = "http://localhost:8001/api/v1/health" },
    @{ Name = "Oswaldo"; Url = "http://localhost:8002/api/v1/health" },
    @{ Name = "Donabedian"; Url = "http://localhost:8003/api/v1/health" },
    @{ Name = "Wanda"; Url = "http://localhost:8004/api/v1/health" },
    @{ Name = "Comunicacao"; Url = "http://localhost:8005/api/v1/health" },
    @{ Name = "Geralda"; Url = "http://localhost:8006/api/v1/health" },
    @{ Name = "Zilda"; Url = "http://localhost:8007/api/v1/health" },
    @{ Name = "Minerva"; Url = "http://localhost:8008/api/v1/health" },
    @{ Name = "Pierre"; Url = "http://localhost:8009/api/v1/health" },
    @{ Name = "Admin"; Url = "http://localhost:8010/api/v1/health" },
    @{ Name = "Gestor"; Url = "http://localhost:8011/api/v1/health" },
    @{ Name = "Grahame"; Url = "http://localhost:8012/api/v1/health" },
    @{ Name = "Nise"; Url = "http://localhost:8013/api/v1/health" },
    @{ Name = "Bridge"; Url = "http://localhost:8014/api/v1/health" },
    @{ Name = "Portal"; Url = "http://localhost:3001/" }
)

$ok = 0
$fail = 0

Write-Host "=== IntelliCare Demo Health Check ==="
Write-Host ""

foreach ($t in $targets) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $t.Url -TimeoutSec $TimeoutSec
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
            Write-Host ("[OK]   {0,-10} {1} -> {2}" -f $t.Name, $t.Url, $resp.StatusCode)
            $ok++
        }
        else {
            Write-Host ("[FAIL] {0,-10} {1} -> {2}" -f $t.Name, $t.Url, $resp.StatusCode)
            $fail++
        }
    }
    catch {
        Write-Host ("[FAIL] {0,-10} {1} -> {2}" -f $t.Name, $t.Url, $_.Exception.Message)
        $fail++
    }
}

Write-Host ""
Write-Host ("Summary: OK={0} FAIL={1}" -f $ok, $fail)

if ($fail -gt 0) {
    exit 1
}

exit 0
