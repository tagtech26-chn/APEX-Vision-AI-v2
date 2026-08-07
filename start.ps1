<#
.SYNOPSIS
    Starts the APEX Vision AI production server (single service: SPA + API).

.DESCRIPTION
    Loads models.env (heavy model paths, created by setup-windows.ps1 /
    download-heavy-models.ps1) if present, then runs uvicorn with a single
    worker. The AI provider defaults to 'auto' (heavy when the models load,
    otherwise the OpenCV heuristic pipeline). Override with e.g.
    $env:APEX_AI_PROVIDER = "heavy" or "light" before running.

.PARAMETER Port
    Port to bind. Default 8000.

.PARAMETER HostAddr
    Address to bind. Default 0.0.0.0 (all interfaces).
#>
param(
    [ValidateRange(1, 65535)][int]$Port = 8000,
    [string]$HostAddr = "0.0.0.0",
    [string]$Python = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path $Python)) { Write-Error "Virtualenv python not found at $Python - run scripts\setup-windows.ps1 first."; exit 1 }

$envFile = Join-Path $Root "models.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
        }
    }
    Write-Host "Loaded model paths from models.env" -ForegroundColor DarkGray
}

if (-not $env:APEX_AI_PROVIDER) {
    Write-Host "APEX_AI_PROVIDER unset - using 'auto' (heavy when models load, else light)." -ForegroundColor DarkGray
}

$dist = Join-Path $Root "frontend\dist"
if (-not (Test-Path $dist)) {
    Write-Warning "frontend\dist not found - the web UI will not be served. Run scripts\setup-windows.ps1 (or 'npm run build' in frontend/) first."
}

Write-Host "Starting APEX Vision AI on http://$HostAddr`:$Port" -ForegroundColor Green
Set-Location $Root
& $Python -m uvicorn app.main:app --host $HostAddr --port $Port --workers 1
