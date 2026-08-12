<#
.SYNOPSIS
    Starts the APEX Vision AI v2.2 server with the geometry advisor.

.PARAMETER GeometryAdvisor
    none or gemini. Gemini requires GEMINI_API_KEY.

.PARAMETER Port
    Port to bind. Default 8010.

.PARAMETER HostAddr
    Address to bind. Default 0.0.0.0.

.PARAMETER Python
    Python executable. Defaults to D:\v22env\Scripts\python.exe when present,
    otherwise the project .venv interpreter.
#>
param(
    [ValidateSet("none", "gemini")][string]$GeometryAdvisor = "none",
    [ValidateRange(1, 65535)][int]$Port = 8010,
    [string]$HostAddr = "0.0.0.0",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not $Python) {
    if (Test-Path "D:\v22env\Scripts\python.exe") {
        $Python = "D:\v22env\Scripts\python.exe"
    } else {
        $Python = Join-Path $Root ".venv\Scripts\python.exe"
    }
}
if (-not (Test-Path $Python)) { throw "Python executable not found: $Python" }

$env:APEX_AI_PROVIDER = "v22"
$env:APEX_GEOMETRY_ADVISOR = $GeometryAdvisor

$envFile = Join-Path $Root "models.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
        }
    }
}

if ($GeometryAdvisor -eq "gemini" -and -not $env:GEMINI_API_KEY) {
    Write-Warning "GeometryAdvisor=gemini but GEMINI_API_KEY is not configured. The advisor will report missing_api_key and the local V2.2 geometry pipeline will continue safely."
}

$frontend = Join-Path $Root "frontend"
$distIndex = Join-Path $frontend "dist\index.html"
$srcFiles = @(Get-ChildItem (Join-Path $frontend "src") -Recurse -File -ErrorAction SilentlyContinue)
$needsBuild = -not (Test-Path $distIndex)
if (-not $needsBuild -and $srcFiles.Count -gt 0) {
    $latestSource = ($srcFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
    $distTime = (Get-Item $distIndex).LastWriteTimeUtc
    $needsBuild = $latestSource -gt $distTime
}

if ($needsBuild) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        Write-Host "Frontend dist is missing/stale; rebuilding..." -ForegroundColor Yellow
        Push-Location $frontend
        try { npm run build } finally { Pop-Location }
    } else {
        Write-Warning "npm is unavailable; existing frontend/dist will be used if present."
    }
}

Write-Host "Starting APEX Vision AI v2.2 on http://$HostAddr`:$Port" -ForegroundColor Green
Write-Host "AI provider: $env:APEX_AI_PROVIDER | Geometry advisor: $env:APEX_GEOMETRY_ADVISOR" -ForegroundColor Cyan
& $Python -m uvicorn app.main:app --host $HostAddr --port $Port --workers 1
