<#
.SYNOPSIS
    One-command production installer for a fresh Windows machine.

.DESCRIPTION
    Creates a .venv, installs every runtime dependency, optionally the heavy
    AI stack (GroundingDINO + SAM2 + Depth-Anything-V2) plus its ~2.9 GB of
    model weights, and builds the React frontend. Afterwards run start.ps1.

    Default (no -Heavy): installs the OpenCV heuristic pipeline only. Works on
    any machine, no extra downloads, runs on CPU. Set APEX_AI_PROVIDER or use
    the model env vars later to switch to the heavy stack.

.PARAMETER Heavy
    Also install the heavy provider source repos (GroundingDINO, SAM2 from git)
    and download the model weights. Requires git and the Visual Studio C++
    Build Tools (groundingdino compiles C++ code). Run with -SkipModels to skip
    the ~2.9 GB weight download.

.PARAMETER CpuOnly
    Install CPU-only torch/torchvision from the PyTorch CPU index. Much smaller
    and faster to install on machines without a GPU. The app runs on CPU either
    way.

.PARAMETER SkipFrontend
    Skip the npm install + production build (requires Node.js >= 20.19). Use it
    when the frontend is already built or Node is not available.

.PARAMETER SkipModels
    With -Heavy: install the heavy code but skip the ~2.9 GB weight download.

.EXAMPLE
    .\scripts\setup-windows.ps1 -CpuOnly
    .\scripts\setup-windows.ps1 -Heavy -CpuOnly
#>
param(
    [switch]$Heavy,
    [switch]$CpuOnly,
    [switch]$SkipFrontend,
    [switch]$SkipModels
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

function Fail($msg) { Write-Error $msg; exit 1 }
function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Test-Exe($name) { (Get-Command $name -ErrorAction SilentlyContinue) -ne $null }

Set-Location $Root
Write-Host "APEX Vision AI - Windows installer" -ForegroundColor Green
Write-Host "Repo root: $Root"

Step "Preflight"
if (-not (Test-Exe "python")) { Fail "Python not found on PATH. Install Python 3.11 and tick 'Add python.exe to PATH'." }
$pyVer = (python --version 2>&1).ToString()
Write-Host "  python: $pyVer"
$pyNum = [version]($pyVer -replace "[^0-9.]", "")
if ($pyNum -lt [version]"3.10") { Fail "Python 3.10+ required (recommended: 3.11). Found: $pyVer" }

if ($Heavy) {
    if (-not (Test-Exe "git")) { Fail "-Heavy needs git on PATH." }
    Write-Host "  git: $(& git --version)" -ForegroundColor DarkGray
    Write-Host "  -Heavy: will build GroundingDINO from source. If the build fails, install" -ForegroundColor Yellow
    Write-Host "    Visual Studio Build Tools with the 'Desktop development with C++' workload" -ForegroundColor Yellow
}
if (-not $SkipFrontend) {
    if (-not (Test-Exe "npm")) { Fail "npm not found on PATH. Install Node.js 20.19+ or rerun with -SkipFrontend." }
    $nodeVer = (node --version).ToString().TrimStart("v")
    $parts = $nodeVer.Split(".")
    $major = [int]$parts[0]; $minor = [int]$parts[1]
    $nodeOk = ($major -gt 22) -or ($major -eq 22 -and $minor -ge 12) -or ($major -eq 20 -and $minor -ge 19)
    Write-Host "  node: v$nodeVer"
    if (-not $nodeOk) { Fail "Node.js 20.19+ or 22.12+ required (Vite 8). Found: v$nodeVer" }
}

Step "Create virtualenv"
if (-not (Test-Path $Python)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) { Fail "Failed to create .venv" }
} else {
    Write-Host "  .venv already exists" -ForegroundColor DarkGray
}

Step "Upgrade pip"
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed" }

if ($CpuOnly) {
    Step "Install CPU-only torch (PyTorch CPU index)"
    & $Python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.13.0" "torchvision==0.28.0"
    if ($LASTEXITCODE -ne 0) { Fail "CPU torch install failed" }
}

Step "Install runtime dependencies (requirements-prod.txt)"
& $Python -m pip install -r requirements-prod.txt
if ($LASTEXITCODE -ne 0) { Fail "pip install requirements-prod.txt failed" }

if ($Heavy) {
    Step "Install heavy AI source repos (GroundingDINO + SAM2)"
    & $Python -m pip install -r requirements-ai-source.txt
    if ($LASTEXITCODE -ne 0) { Fail "pip install requirements-ai-source.txt failed" }

    if (-not $SkipModels) {
        Step "Download heavy model weights (~2.9 GB)"
        & (Join-Path $Root "scripts\download-heavy-models.ps1")
        if ($LASTEXITCODE -ne 0) { Fail "Model download failed" }
    } else {
        Write-Host "  -SkipModels: run scripts\download-heavy-models.ps1 later to fetch the weights." -ForegroundColor Yellow
    }
}

if (-not $SkipFrontend) {
    Step "Build frontend (npm ci + npm run build)"
    Push-Location (Join-Path $Root "frontend")
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { Fail "npm ci failed" }
        npm run build
        if ($LASTEXITCODE -ne 0) { Fail "npm run build failed" }
    } finally {
        Pop-Location
    }
}

Step "Installation complete"
$provider = if ($Heavy) { "heavy (production default)" } else { "light (heuristic OpenCV pipeline)" }
Write-Host "  AI provider: $provider"
Write-Host ""
Write-Host "  Start the server:" -ForegroundColor Green
Write-Host "      .\start.ps1"
Write-Host "  Then open http://127.0.0.1:8000 in a browser." -ForegroundColor Green