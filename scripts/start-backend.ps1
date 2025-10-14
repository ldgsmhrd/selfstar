param(
  [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$venv = Join-Path $backendDir '.venv'
$pythonExe = Join-Path $venv 'Scripts/python.exe'
.$PSScriptRoot/utils.ps1

Write-Host "[backend] working dir: $backendDir"
Push-Location $backendDir
try {
  if (!(Test-Path $pythonExe)) {
    Write-Host '[backend] creating venv'
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { python -m venv .venv }
    else { throw 'Python not found. Install Python 3.10+ and ensure it is on PATH.' }
  }

  & $pythonExe -m pip install --upgrade pip setuptools wheel

  $req = 'requirements.txt'
  if (Test-Path $req) {
    Write-Host '[backend] installing requirements'
    & $pythonExe -m pip install -r $req
  }

  Stop-ProcessOnPort -Port $Port
  Write-Host "[backend] starting uvicorn on port $Port"
  & $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}
finally {
  Pop-Location
}
