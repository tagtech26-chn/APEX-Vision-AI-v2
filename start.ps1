<#
.SYNOPSIS
    Starts the APEX Vision AI production server (single service: SPA + API).

.DESCRIPTION
    Loads models.env (heavy model paths, created by setup-windows.ps1 /
    download-heavy-models.ps1) if present, then runs uvicorn with a single
    worker. Production defaults to the Heavy AI provider. Set
    APEX_AI_PROVIDER=auto or light explicitly when a fallback is required.

    A local cache signing key is generated once when one is not supplied.
    This enables the existing integrity-protected scene cache without
    committing a machine-specific secret to the repository.

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
    $env:APEX_AI_PROVIDER = "heavy"
    Write-Host "APEX_AI_PROVIDER unset - using production Heavy AI." -ForegroundColor DarkGray
}
if (-not $env:APEX_AI_DEVICE) {
    $env:APEX_AI_DEVICE = "auto"
    Write-Host "APEX_AI_DEVICE unset - selecting CUDA when available, otherwise CPU." -ForegroundColor DarkGray
}

# Enable the existing HMAC-protected scene cache for local Windows runs.
# The key is machine-local and intentionally ignored by Git.
if (-not $env:APEX_CACHE_SIGNING_KEY) {
    $cacheKeyFile = Join-Path $Root ".apex-cache-signing-key"
    if (Test-Path $cacheKeyFile) {
        $env:APEX_CACHE_SIGNING_KEY = (Get-Content $cacheKeyFile -Raw).Trim()
    }
    else {
        $bytes = New-Object byte[] 32
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        try {
            $rng.GetBytes($bytes)
        }
        finally {
            $rng.Dispose()
        }
        $env:APEX_CACHE_SIGNING_KEY = [Convert]::ToBase64String($bytes)
        Set-Content -Path $cacheKeyFile -Value $env:APEX_CACHE_SIGNING_KEY -NoNewline
    }
    Write-Host "Scene analysis cache enabled with local signing key." -ForegroundColor DarkGray
}

$dist = Join-Path $Root "frontend\dist"
if (-not (Test-Path $dist)) {
    Write-Warning "frontend\dist not found - the web UI will not be served. Run scripts\setup-windows.ps1 (or 'npm run build' in frontend/) first."
}

Write-Host "Starting APEX Vision AI on http://$HostAddr`:$Port" -ForegroundColor Green
Write-Host "AI Provider: $env:APEX_AI_PROVIDER | Device: $env:APEX_AI_DEVICE" -ForegroundColor Cyan
Set-Location $Root
& $Python -m uvicorn app.main:app --host $HostAddr --port $Port --workers 1
