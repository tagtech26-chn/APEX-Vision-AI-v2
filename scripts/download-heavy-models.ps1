<#
.SYNOPSIS
    Downloads the heavy AI model weights and writes models.env.

.DESCRIPTION
    Downloads GroundingDINO, SAM2.1 and Depth-Anything-V2 checkpoints (~2.9 GB
    total) into <repo>\models\, clones the Depth-Anything-V2 source repo, and
    writes models.env at the repo root with the paths start.ps1 needs to set
    for the heavy provider.

.PARAMETER ModelsDir
    Where to store the checkpoints and the Depth-Anything-V2 clone.
    Default: <repo>\models

.PARAMETER VenvPython
    Path to the virtualenv python.exe used to locate the pip-installed
    GroundingDINO / SAM2 config files. Default: <repo>\.venv\Scripts\python.exe
#>
param(
    [string]$ModelsDir = (Join-Path (Split-Path -Parent $PSScriptRoot) "models"),
    [string]$VenvPython = (Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\python.exe"),
    [string]$EnvFile = (Join-Path (Split-Path -Parent $PSScriptRoot) "models.env")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Fail($msg) { Write-Error $msg; exit 1 }

function Download-File {
    param([string]$Url, [string]$Destination)
    if (Test-Path $Destination) {
        Write-Host "  already present: $Destination" -ForegroundColor DarkGray
        return
    }
    Write-Host "  downloading $([System.IO.Path]::GetFileName($Destination))"
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & $curl.Source -L -C - --retry 3 --retry-delay 5 -o $Destination $Url
        if ($LASTEXITCODE -ne 0) { Fail "Download failed (curl): $Url" }
    } else {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -TimeoutSec 1800
    }
    if (-not (Test-Path $Destination)) { Fail "Download produced no file: $Url" }
}

Write-Host "==> Downloading heavy AI models to $ModelsDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null

Download-File "https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth" (Join-Path $ModelsDir "groundingdino_swint_ogc.pth")
Download-File "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt" (Join-Path $ModelsDir "sam2.1_hiera_large.pt")
Download-File "https://huggingface.co/depth-anything/Depth-Anything-V2-Large/resolve/main/depth_anything_v2_vitl.pth" (Join-Path $ModelsDir "depth_anything_v2_vitl.pth")

Write-Host "==> Cloning Depth-Anything-V2 source" -ForegroundColor Cyan
$da2Dir = Join-Path $ModelsDir "Depth-Anything-V2"
if (-not (Test-Path $da2Dir)) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { Fail "git not found on PATH - required to clone Depth-Anything-V2." }
    & $git.Source clone --depth 1 https://github.com/DepthAnything/Depth-Anything-V2.git $da2Dir
    if ($LASTEXITCODE -ne 0) { Fail "git clone failed for Depth-Anything-V2." }
} else {
    Write-Host "  already present: $da2Dir" -ForegroundColor DarkGray
}

Write-Host "==> Resolving pip-installed config paths" -ForegroundColor Cyan
$site = if (Test-Path $VenvPython) {
    & $VenvPython -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>$null
} else { $null }
if (-not $site) {
    $site = Join-Path (Split-Path -Parent (Split-Path -Parent $VenvPython)) "Lib\site-packages"
}
$gdinoConfig = Join-Path $site "groundingdino\config\GroundingDINO_SwinT_OGC.py"
$sam2ConfigDir = Join-Path $site "sam2\configs"
if (-not (Test-Path $gdinoConfig)) { Write-Warning "GroundingDINO config not found at $gdinoConfig - is groundingdino installed in $VenvPython ?" }
if (-not (Test-Path $sam2ConfigDir)) { Write-Warning "SAM2 configs not found at $sam2ConfigDir - is SAM_2 installed in $VenvPython ?" }

$envContent = @(
    "GROUNDING_DINO_CONFIG=$gdinoConfig",
    "GROUNDING_DINO_CKPT=$(Join-Path $ModelsDir 'groundingdino_swint_ogc.pth')",
    "SAM2_CONFIG_DIR=$sam2ConfigDir",
    "SAM2_CONFIG_FILE=sam2.1/sam2.1_hiera_l.yaml",
    "SAM2_CKPT=$(Join-Path $ModelsDir 'sam2.1_hiera_large.pt')",
    "DEPTH_ANYTHING_ROOT=$da2Dir",
    "DEPTH_ANYTHING_CKPT=$(Join-Path $ModelsDir 'depth_anything_v2_vitl.pth')"
)
$envContent | Set-Content -Path $EnvFile -Encoding UTF8
Write-Host "Wrote $EnvFile (loaded automatically by start.ps1)" -ForegroundColor Green

$total = (Get-ChildItem $ModelsDir -Filter *.pth | Measure-Object Length -Sum).Sum / 1GB
Write-Host ("Model weights: {0:N2} GB" -f $total)
Write-Host "Done. Run .\start.ps1 (or start.ps1 with APEX_AI_PROVIDER=heavy)." -ForegroundColor Green
