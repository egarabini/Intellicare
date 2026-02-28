param(
    [int]$TimeoutSec = 5
)

$targets = @(
    @{ Name = "Nise"; Url = "http://localhost:8000/health" },
    @{ Name = "Florence"; Url = "http://localhost:8001/health" },
    @{ Name = "Oswaldo"; Url = "http://localhost:8002/health" },
    @{ Name = "Zilda"; Url = "http://localhost:8003/api/v1/health" },
    @{ Name = "Grahame"; Url = "http://localhost:8004/api/v1/health" },
    @{ Name = "Geralda"; Url = "http://localhost:8006/api/v1/health" },
    @{ Name = "Portal"; Url = "http://localhost:5173/" }
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
        } else {
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
