[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$Room = 1,
    [int]$Tile = 1,
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd('/')

function Get-Json([string]$Url) {
    try {
        return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 20
    } catch {
        throw "GET $Url failed: $($_.Exception.Message)"
    }
}

Write-Host "APEX Vision AI production validation" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"

$health = Get-Json "$BaseUrl/api/health"
if ($health.status -ne "ok") { throw "Health check failed." }
Write-Host "[PASS] /api/health" -ForegroundColor Green

$readyResponse = $null
try {
    $readyResponse = Invoke-WebRequest -Uri "$BaseUrl/api/ready" -Method Get -TimeoutSec 20
} catch {
    $readyResponse = $_.Exception.Response
    if ($null -eq $readyResponse) { throw }
}

$readyBody = $readyResponse.Content | ConvertFrom-Json
if ($readyResponse.StatusCode -ne 200 -or $readyBody.status -ne "ready") {
    Write-Host "[FAIL] /api/ready" -ForegroundColor Red
    $readyBody | ConvertTo-Json -Depth 8
    throw "Production runtime is not ready. Install/configure every reported Heavy dependency and checkpoint, then restart."
}
Write-Host "[PASS] /api/ready provider=$($readyBody.ai_provider)" -ForegroundColor Green

$diagnostics = Get-Json "$BaseUrl/api/diagnostics"
if ($diagnostics.success -ne $true) { throw "Diagnostics endpoint did not report success." }
if ($diagnostics.ai.configured_provider -ne $readyBody.ai_provider) {
    throw "Provider mismatch between readiness and diagnostics."
}
Write-Host "[PASS] /api/diagnostics provider=$($diagnostics.ai.configured_provider)" -ForegroundColor Green

$rooms = Get-Json "$BaseUrl/api/rooms"
$catalog = Get-Json "$BaseUrl/api/catalog/tiles"
if ($null -eq $rooms -or $null -eq $catalog) { throw "Room/catalog API returned no data." }
Write-Host "[PASS] Room and tile catalog APIs" -ForegroundColor Green

$payload = @{
    room = $Room
    tile = $Tile
    tile_size = 600
    grout_width = 2
    grout_color = @(220,220,220)
    pattern = "Straight"
    material_profile = "generic"
} | ConvertTo-Json

try {
    $queued = Invoke-RestMethod -Uri "$BaseUrl/api/render" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
} catch {
    throw "Render submission failed: $($_.Exception.Message)"
}

if ([string]::IsNullOrWhiteSpace($queued.job_id)) { throw "Render endpoint did not return a job_id." }
Write-Host "[PASS] Render submitted job=$($queued.job_id)" -ForegroundColor Green

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    $job = Get-Json "$BaseUrl/api/render/$($queued.job_id)"
    Write-Host ("  {0} {1:P0} {2}" -f $job.status, [double]$job.progress, $job.message)

    if ($job.status -eq "done") {
        if ([string]::IsNullOrWhiteSpace($job.image)) { throw "Render completed without an output image." }
        $output = Invoke-WebRequest -Uri "$BaseUrl$($job.image)" -Method Head -TimeoutSec 20
        if ($output.StatusCode -ne 200) { throw "Rendered output is not accessible: $($job.image)" }
        Write-Host "[PASS] Heavy end-to-end render output: $($job.image)" -ForegroundColor Green
        Write-Host "VALIDATION COMPLETE: backend + Heavy readiness + catalog + render + output delivery passed." -ForegroundColor Green
        exit 0
    }

    if ($job.status -eq "error") {
        throw "Render job failed. Check server logs for the detailed exception."
    }
}

throw "Render validation timed out after $TimeoutSeconds seconds."
