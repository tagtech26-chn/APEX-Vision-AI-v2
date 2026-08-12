$ErrorActionPreference = "Stop"

$python = $env:APEX_V22_PYTHON
if (-not $python) { $python = "D:\v22env\Scripts\python.exe" }
if (-not (Test-Path $python)) { $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe" }
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "Using v2.2 Python: $python"

Write-Host "`n[1/4] Python version"
& $python --version

Write-Host "`n[2/4] Compile all Python sources"
& $python -m compileall -q app tests

Write-Host "`n[3/4] Metric floor regression"
& $python -m pytest -q tests/test_v22_metric_floor.py

Write-Host "`n[4/4] Provider import smoke"
$env:APEX_AI_PROVIDER = "v22"
& $python -c "from app.ai.scene.analyzer import build_scene_analyzer; a=build_scene_analyzer('v22'); print('provider=', a.__class__.__name__); print('providers=', a.providers)"

Write-Host "`nV2.2 validation PASSED." -ForegroundColor Green
