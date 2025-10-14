param(
  [int]$Port = 8600
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$aiDir = Join-Path $repoRoot 'ai'
$venv = Join-Path $aiDir '.venv'
$pythonExe = Join-Path $venv 'Scripts/python.exe'
.$PSScriptRoot/utils.ps1

Write-Host "[ai] working dir: $aiDir"
Push-Location $aiDir
try {
  if (!(Test-Path $pythonExe)) {
    Write-Host '[ai] creating venv'
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { python -m venv .venv }
    else { throw 'Python not found. Install Python 3.10+ and ensure it is on PATH.' }
  }
  & $pythonExe -m pip install --upgrade pip setuptools wheel
  # Optional dependency: google-genai only if API key is present
  if ($env:GOOGLE_API_KEY) {
    try { & $pythonExe -c "import google.genai" 2>$null } catch { }
    if ($LASTEXITCODE -ne 0) { & $pythonExe -m pip install google-genai }
  }
  if (Test-Path 'requirements-serving.txt') {
    Write-Host '[ai] installing requirements-serving (lightweight)'
    & $pythonExe -m pip install -r 'requirements-serving.txt'
  } elseif (Test-Path 'requirements.txt') {
    Write-Host '[ai] installing requirements'
    & $pythonExe -m pip install -r 'requirements.txt'
  } elseif (Test-Path 'requirements-ml.txt') {
    Write-Host '[ai] installing requirements-ml'
    & $pythonExe -m pip install -r 'requirements-ml.txt'
  }
  Stop-ProcessOnPort -Port $Port
  Write-Host "[ai] starting uvicorn on port $Port"
  # Ensure 'ai' package is importable when launched from the ai folder
  $env:PYTHONPATH = $repoRoot
  & $pythonExe -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port $Port
}
finally {
  Pop-Location
}
